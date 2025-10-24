import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np  # Necesario para cálculos IQR si pandas < 1.0

from crud import abastecimiento as abastecimiento_crud
from crud import prediccion as prediccion_crud
# Asegúrate de importar el modelo correcto
from db import models

# Mínimo de registros para predicción y cálculo de uso diario
MIN_RECORDS_PREDICTION = 3
MIN_RECORDS_USAGE = 2


def calculate_prediction(db: Session, id_sitio: int):
    """
    Calcula la fecha del próximo abastecimiento con lógica mejorada y
    guarda o actualiza el resultado en la base de datos.
    """
    # 1. Obtener Historial (ordenado por fecha ASCENDENTE para cálculos diff)
    history = db.query(models.Abastecimiento) \
        .filter(models.Abastecimiento.id_sitio == id_sitio) \
        .order_by(models.Abastecimiento.fecha.asc()) \
        .all()

    if len(history) < MIN_RECORDS_PREDICTION:
        return {
            "error": f"Se necesitan al menos {MIN_RECORDS_PREDICTION} registros históricos para una predicción fiable."}

    # 2. Preparar DataFrame
    df = pd.DataFrame([h.__dict__ for h in history])
    # Convertir 'fecha' a datetime si no lo está
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.sort_values(by='fecha').reset_index(drop=True)

    # --- 3. CORRECCIÓN: Calcular Consumo por Intervalo ---
    df['horometraje_diff'] = df['horometraje'].diff()
    # Nivel de combustible *después* de cada abastecimiento
    df['nivel_combustible_post'] = df['gls_existentes'] + df['gls_abastecidos']
    # Consumo = Nivel post abastecimiento anterior - Nivel pre abastecimiento actual
    df['gls_consumidos'] = df['nivel_combustible_post'].shift(1) - df['gls_existentes']

    # 4. Limpiar Datos
    df_cleaned = df.dropna(subset=['horometraje_diff', 'gls_consumidos'])
    # Solo intervalos con aumento de horometraje y consumo positivo
    df_cleaned = df_cleaned[(df_cleaned['horometraje_diff'] > 0) & (df_cleaned['gls_consumidos'] > 0)]

    if df_cleaned.empty or len(df_cleaned) < 2:  # Necesitamos al menos 2 intervalos para regresión/media
        return {"error": "No se pudieron calcular suficientes intervalos de consumo válidos."}

    # 5. Calcular Tasa de Consumo por Intervalo
    df_cleaned['tasa_periodo'] = df_cleaned['gls_consumidos'] / df_cleaned['horometraje_diff']

    # 6. Filtrar Outliers (IQR)
    Q1 = df_cleaned['tasa_periodo'].quantile(0.25)
    Q3 = df_cleaned['tasa_periodo'].quantile(0.75)
    IQR = Q3 - Q1
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR
    df_sin_outliers = df_cleaned[
        (df_cleaned['tasa_periodo'] >= limite_inferior) & (df_cleaned['tasa_periodo'] <= limite_superior)]

    if len(df_sin_outliers) < 1:  # Necesitamos al menos 1 tasa válida
        return {"error": "Después de filtrar datos atípicos, no quedan tasas de consumo válidas."}
    elif len(df_sin_outliers) < 2:  # Si solo queda 1, usamos su tasa directamente
        tasa_consumo_gls_por_hora = df_sin_outliers['tasa_periodo'].iloc[0]
    else:
        # 7. Regresión Lineal (si hay suficientes datos)
        if df_sin_outliers['horometraje_diff'].nunique() < 2:
            # Si todas las diferencias de horometraje son iguales, usar la media
            tasa_consumo_gls_por_hora = df_sin_outliers['tasa_periodo'].mean()
        else:
            X = df_sin_outliers[['horometraje_diff']]
            y = df_sin_outliers['gls_consumidos']
            model = LinearRegression()
            model.fit(X, y)
            tasa_consumo_gls_por_hora = model.coef_[0]

    if tasa_consumo_gls_por_hora <= 0:
        return {"error": f"Tasa de consumo no válida calculada: {tasa_consumo_gls_por_hora:.2f} Gls/Hr"}

    print(f"-> Tasa de consumo estimada para sitio {id_sitio}: {tasa_consumo_gls_por_hora:.2f} Gls/Hr")  # DEBUG

    # --- 8. CORRECCIÓN: Combustible Actual ---
    # Es el nivel *después* del último abastecimiento registrado
    ultimo_abastecimiento = history[-1]  # El último en la lista ordenada por fecha
    galones_actuales = ultimo_abastecimiento.gls_existentes + ultimo_abastecimiento.gls_abastecidos

    if galones_actuales <= 0:
        return {"error": "El último registro indica 0 galones después del abastecimiento."}

    horas_restantes = galones_actuales / tasa_consumo_gls_por_hora
    print(f"-> Galones actuales: {galones_actuales:.2f}, Horas restantes estimadas: {horas_restantes:.2f}")  # DEBUG

    # --- 9. REEMPLAZO: Calcular Uso Diario Dinámico ---
    if len(history) >= MIN_RECORDS_USAGE:
        primer_registro = history[0]
        ultimo_registro = history[-1]

        # Asegurarse que las fechas son objetos datetime
        fecha_primera = primer_registro.fecha
        fecha_ultima = ultimo_registro.fecha
        if not isinstance(fecha_primera, datetime) or not isinstance(fecha_ultima, datetime):
            return {"error": "Fechas inválidas en el historial para calcular uso diario."}

        dias_totales = (fecha_ultima - fecha_primera).total_seconds() / (60 * 60 * 24)
        horometraje_diff_total = ultimo_registro.horometraje - primer_registro.horometraje

        if dias_totales < 1 or horometraje_diff_total <= 0:  # Evitar división por cero o uso no positivo
            # Si no hay suficientes días o uso, usar un valor por defecto o devolver error
            # Podríamos intentar con un periodo más corto si hay suficientes datos
            print(
                f"-> No se pudo calcular uso diario fiable (Días: {dias_totales:.1f}, Horas usadas: {horometraje_diff_total:.1f}). Usando valor por defecto.")  # DEBUG
            uso_diario_horas = 8  # Valor por defecto si falla el cálculo
        else:
            uso_diario_horas = horometraje_diff_total / dias_totales
            # Limitar a un máximo razonable para evitar valores extremos si hay pocos días
            uso_diario_horas = min(uso_diario_horas, 24)
            print(f"-> Uso diario calculado: {uso_diario_horas:.2f} Hrs/Día")  # DEBUG
    else:
        print(
            f"-> No hay suficientes registros ({len(history)}) para calcular uso diario. Usando valor por defecto.")  # DEBUG
        uso_diario_horas = 8  # Valor por defecto si no hay suficientes datos

    # Asegurar que uso_diario_horas no sea cero para evitar división infinita
    if uso_diario_horas <= 0:
        uso_diario_horas = 0.1  # Un valor muy pequeño para evitar error, implica bajo uso

    dias_restantes = horas_restantes / uso_diario_horas
    print(f"-> Días restantes estimados: {dias_restantes:.2f}")  # DEBUG

    # 10. Cálculo de Fechas y Horometraje Final (sin cambios)
    horometro_actual = ultimo_abastecimiento.horometraje
    horometro_estimado_fin = horometro_actual + horas_restantes
    fecha_ultimo_abastecimiento = ultimo_abastecimiento.fecha
    fecha_proximo_abastecimiento = fecha_ultimo_abastecimiento + timedelta(days=dias_restantes)

    # 11. Guardar/Actualizar Predicción
    data_para_guardar = {
        "id_sitio": id_sitio,
        "fecha_proximo_abastecimiento": fecha_proximo_abastecimiento,
        "id_ultimo_abastecimiento_usado": ultimo_abastecimiento.id_abastecimiento,
        "horometro_estimado_fin": round(horometro_estimado_fin, 2)
    }
    db_prediction_object = prediccion_crud.create_or_update_prediccion(db, prediccion_data=data_para_guardar)

    # 12. Devolver Resultado
    return db_prediction_object