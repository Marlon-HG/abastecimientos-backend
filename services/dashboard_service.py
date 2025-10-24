# services/dashboard_service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, cast, Date as SQLDate
from datetime import datetime, timedelta
import pytz # Importar pytz para manejar zonas horarias
from db import models
from typing import Optional, List, Dict, Any

def get_dashboard_stats(db: Session, current_user: models.Usuario) -> Dict[str, Any]:
    """
    Calcula estadísticas clave para el dashboard basadas en el rol del usuario,
    usando la hora de Guatemala.
    """
    # --- Obtener usuario y roles (sin cambios) ---
    user_with_roles = db.query(models.Usuario).options(
        joinedload(models.Usuario.roles),
        joinedload(models.Usuario.tecnico)
    ).filter(models.Usuario.id_usuario == current_user.id_usuario).first()

    if not user_with_roles: return {"error": "Usuario no encontrado"}
    user_roles = {rol.nombre for rol in user_with_roles.roles}
    is_admin = 'ADMIN' in user_roles
    is_supervisor = 'SUPERVISOR' in user_roles
    is_tecnico = 'TECNICO' in user_roles
    tecnico_id = user_with_roles.tecnico.id_tecnico if is_tecnico and user_with_roles.tecnico else None

    # --- CORRECCIÓN: Usar zona horaria de Guatemala ---
    guatemala_tz = pytz.timezone('America/Guatemala')
    now = datetime.now(guatemala_tz) # Obtener hora actual en Guatemala
    # Asegurarse que las fechas de la BD sean comparables (naive vs aware)
    # Si las fechas de la BD son naive (sin zona horaria), comparar con now.replace(tzinfo=None)
    # Si las fechas de la BD son aware (con zona horaria, ej UTC), convertir 'now' a UTC: now_utc = now.astimezone(pytz.utc)
    # Asumiremos por ahora que las fechas de BD son naive o se manejan correctamente en la comparación.
    # --- FIN CORRECCIÓN ---

    stats: Dict[str, Any] = {}
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    hace_30_dias = now - timedelta(days=30)
    # Define tu umbral crítico (ej: necesita abastecimiento en menos de 3 días desde AHORA)
    limite_critico = now + timedelta(days=3)

    # --- Definir queries base (sin cambios) ---
    base_query_sitios = db.query(models.Sitio)
    query_abast_mes = db.query(models.Abastecimiento).filter(
        models.Abastecimiento.fecha >= inicio_mes.replace(tzinfo=None), # Comparar naive si fecha en BD es naive
        models.Abastecimiento.status == 'ACTIVO'
    )
    query_abast_30d = db.query(models.Abastecimiento).filter(
        models.Abastecimiento.fecha >= hace_30_dias.replace(tzinfo=None), # Comparar naive
        models.Abastecimiento.status == 'ACTIVO'
    )
    # Comparar now_naive con fecha_proximo_abastecimiento (asumiendo naive en BD)
    now_naive = now.replace(tzinfo=None)
    limite_critico_naive = limite_critico.replace(tzinfo=None)
    query_proximos_7d = db.query(models.PrediccionAbastecimiento).filter(
        models.PrediccionAbastecimiento.fecha_proximo_abastecimiento >= now_naive,
        models.PrediccionAbastecimiento.fecha_proximo_abastecimiento < now_naive + timedelta(days=7)
    )
    query_alertas_abiertas = db.query(models.Alerta).filter(
        models.Alerta.estado_alerta.in_([models.EstadoAlertaEnum.ABIERTA, models.EstadoAlertaEnum.ENVIADA])
    )
    query_sitios_criticos = db.query(models.PrediccionAbastecimiento).options(
        joinedload(models.PrediccionAbastecimiento.sitio)
    ).filter(
        models.PrediccionAbastecimiento.fecha_proximo_abastecimiento < limite_critico_naive,
        models.PrediccionAbastecimiento.fecha_proximo_abastecimiento >= now_naive
    )

    # --- Aplicar filtros por rol (sin cambios) ---
    if is_tecnico and tecnico_id:
        base_query_sitios = base_query_sitios.filter(models.Sitio.id_tecnico == tecnico_id)
        query_abast_mes = query_abast_mes.join(models.Sitio).filter(models.Sitio.id_tecnico == tecnico_id)
        query_abast_30d = query_abast_30d.join(models.Sitio).filter(models.Sitio.id_tecnico == tecnico_id)
        query_proximos_7d = query_proximos_7d.join(models.Sitio).filter(models.Sitio.id_tecnico == tecnico_id)
        query_alertas_abiertas = query_alertas_abiertas.join(models.Sitio).filter(models.Sitio.id_tecnico == tecnico_id)
        query_sitios_criticos = query_sitios_criticos.join(models.Sitio).filter(models.Sitio.id_tecnico == tecnico_id)
    elif is_admin or is_supervisor:
        pass
    else: # Sin rol válido
        return {
            "total_sitios": 0, "total_abastecimientos_mes": 0, "total_galones_mes": 0.0,
            "sitios_proximo_abastecimiento": 0, "alertas_abiertas": 0,
            "total_galones_ultimos_30_dias": 0.0, "abastecimientos_ultimos_30_dias": 0,
            "sitios_criticos": [], "ultimos_abastecimientos": [],
            "sitios_menor_nivel": [], "galones_por_dia_chart": []
        }

    # --- Ejecutar queries (sin cambios) ---
    stats["total_sitios"] = base_query_sitios.count()
    stats["total_abastecimientos_mes"] = query_abast_mes.count()
    stats["total_galones_mes"] = query_abast_mes.with_entities(func.sum(models.Abastecimiento.gls_abastecidos)).scalar() or 0.0
    stats["sitios_proximo_abastecimiento"] = query_proximos_7d.count()
    stats["alertas_abiertas"] = query_alertas_abiertas.count()
    stats["total_galones_ultimos_30_dias"] = query_abast_30d.with_entities(func.sum(models.Abastecimiento.gls_abastecidos)).scalar() or 0.0
    stats["abastecimientos_ultimos_30_dias"] = query_abast_30d.count()

    # --- Procesar lista de sitios críticos con Debugging y cálculo de días ---
    predicciones_criticas = query_sitios_criticos.order_by(
        models.PrediccionAbastecimiento.fecha_proximo_abastecimiento.asc()
    ).limit(5).all()

    sitios_criticos_list = []
    print("\n--- DEBUG: Procesando Sitios Críticos ---") # DEBUG INICIO
    for pred in predicciones_criticas:
        print(f"Procesando Predicción ID: {pred.id_prediccion}, Sitio ID: {pred.id_sitio}") # DEBUG
        if pred.sitio and pred.fecha_proximo_abastecimiento:
            # Asegurarse que pred.fecha_proximo_abastecimiento sea naive si 'now' es naive para la resta
            fecha_prox_naive = pred.fecha_proximo_abastecimiento # Asumimos naive de BD
            now_calc = now_naive # Usar now_naive para calcular diferencia

            print(f"  Fecha Próx. Abast. (naive): {fecha_prox_naive} (Tipo: {type(fecha_prox_naive)})") # DEBUG
            print(f"  Fecha Actual (naive calc): {now_calc} (Tipo: {type(now_calc)})") # DEBUG

            try:
                # Calcular diferencia entre fechas naive
                time_difference = fecha_prox_naive - now_calc
                print(f"  Time Difference: {time_difference}") # DEBUG

                dias_restantes_float = time_difference.total_seconds() / (60 * 60 * 24)
                print(f"  Días Restantes (float): {dias_restantes_float}") # DEBUG

                # Redondear si es >= 0
                dias_restantes_rounded = round(dias_restantes_float, 1) if dias_restantes_float >= 0 else 0.0
                print(f"  Días Restantes (rounded): {dias_restantes_rounded}") # DEBUG

                resultado_dias = dias_restantes_rounded

            except Exception as e:
                print(f"!!!!!! ERROR calculando días restantes: {e} !!!!!!") # DEBUG ERROR
                resultado_dias = None

            sitios_criticos_list.append({
                "id_sitio": pred.sitio.id_sitio,
                "nombre_sitio": pred.sitio.nombre,
                "fecha_proximo_abastecimiento": pred.fecha_proximo_abastecimiento.strftime('%d/%m/%Y'), # Mostrar fecha original
                "dias_restantes": resultado_dias
            })
        else:
             print(f"  Datos incompletos: pred.sitio={pred.sitio}, pred.fecha_proximo_abastecimiento={pred.fecha_proximo_abastecimiento}") # DEBUG ELSE
             sitios_criticos_list.append({
                "id_sitio": pred.id_sitio if pred else 'N/A',
                "nombre_sitio": "Nombre no disponible",
                "fecha_proximo_abastecimiento": "N/A",
                "dias_restantes": None
            })
    print("--- DEBUG: Fin Procesando Sitios Críticos ---\n") # DEBUG FIN

    stats["sitios_criticos"] = sitios_criticos_list

    # --- Últimos 5 Abastecimientos (sin cambios) ---
    query_ultimos = query_abast_mes.options(
         joinedload(models.Abastecimiento.sitio)
    ).order_by(desc(models.Abastecimiento.fecha)).limit(5)
    ultimos_abastecimientos = query_ultimos.all()
    stats["ultimos_abastecimientos"] = [
        {
            "id_abastecimiento": ab.id_abastecimiento,
            "nombre_sitio": ab.sitio.nombre if ab.sitio else "N/A",
            "fecha": ab.fecha.strftime('%d/%m/%Y %H:%M') if ab.fecha else "N/A", # Asume fecha naive
            "galones_abastecidos": ab.gls_abastecidos
        } for ab in ultimos_abastecimientos
    ]

    # --- Datos para Gráfico (sin cambios) ---
    galones_por_dia = query_abast_30d.with_entities(
        cast(models.Abastecimiento.fecha, SQLDate).label('dia_label'),
        func.sum(models.Abastecimiento.gls_abastecidos).label('galones_value')
    ).group_by(cast(models.Abastecimiento.fecha, SQLDate)).order_by(cast(models.Abastecimiento.fecha, SQLDate)).all()
    stats["galones_por_dia_chart"] = [
        {"label": dia.strftime('%Y-%m-%d'), "value": total_galones or 0.0}
        for dia, total_galones in galones_por_dia
    ]

    stats["sitios_menor_nivel"] = [] # Placeholder

    return stats