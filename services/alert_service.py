import traceback
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from db import models
from crud import sitio as sitio_crud, alerta as alerta_crud
from schemas import alerta as alerta_schema
from services import prediction_service
from core import email_service
from db.models import TipoAlertaEnum, EstadoAlertaEnum, CanalEnvioEnum, EstadoEnvioEnum
from crud import notificacion as notificacion_crud
from schemas import notificacion as notificacion_schema

UMBRAL_DIAS_CRITICO = 7
UMBRAL_DIAS_ADVERTENCIA = 14


async def generar_alertas_de_predicciones(db: Session):
    """
    Calcula predicciones y genera/actualiza alertas, notificando si es necesario.
    """
    sitios = sitio_crud.get_sitios(db)
    nuevas_alertas_generadas = 0
    alertas_actualizadas = 0
    fecha_actual = datetime.now()

    print(f"--- Iniciando generación de alertas para {len(sitios)} sitios ---")

    for sitio in sitios:
        sitio_con_relaciones = db.query(models.Sitio).options(
            joinedload(models.Sitio.tecnico).joinedload(models.Tecnico.usuario)
        ).filter(models.Sitio.id_sitio == sitio.id_sitio).first()

        if not sitio_con_relaciones:
            print(f"\nError: No se pudo recargar el sitio ID: {sitio.id_sitio}")
            continue

        print(f"\nProcesando sitio ID: {sitio_con_relaciones.id_sitio}, Nombre: {sitio_con_relaciones.nombre}")

        # --- PASO A: Calcular Predicción ---
        resultado_prediccion = prediction_service.calculate_prediction(db, id_sitio=sitio_con_relaciones.id_sitio)
        print(f"Resultado predicción: {resultado_prediccion}")

        if isinstance(resultado_prediccion, dict) and "error" in resultado_prediccion:
            print(f"-> Error en predicción: {resultado_prediccion['error']}")
            continue
        if not isinstance(resultado_prediccion, models.PrediccionAbastecimiento):
            print(f"-> Predicción inválida.")
            continue

        prediccion_actualizada = resultado_prediccion

        # --- PASO B: Determinar Tipo de Alerta ---
        if not isinstance(prediccion_actualizada.fecha_proximo_abastecimiento, datetime):
            print(f"-> Fecha de predicción inválida.")
            continue

        dias_restantes = (prediccion_actualizada.fecha_proximo_abastecimiento - fecha_actual).days
        print(f"-> Días restantes calculados: {dias_restantes}")

        tipo_alerta = None
        mensaje = ""
        if dias_restantes < 0:
            tipo_alerta = TipoAlertaEnum.CRITICA
            mensaje = f"Nivel CRITICO. Fecha estimada de agotamiento ya pasó ({prediccion_actualizada.fecha_proximo_abastecimiento.strftime('%Y-%m-%d')}). Revisar urgentemente."
        elif dias_restantes <= UMBRAL_DIAS_CRITICO:
            tipo_alerta = TipoAlertaEnum.CRITICA
            mensaje = f"Nivel CRITICO. Se estiman {dias_restantes} días de combustible restantes (hasta {prediccion_actualizada.fecha_proximo_abastecimiento.strftime('%Y-%m-%d')})."
        elif dias_restantes <= UMBRAL_DIAS_ADVERTENCIA:
            tipo_alerta = TipoAlertaEnum.ADVERTENCIA
            mensaje = f"Nivel ADVERTENCIA. Se estiman {dias_restantes} días de combustible restantes (hasta {prediccion_actualizada.fecha_proximo_abastecimiento.strftime('%Y-%m-%d')})."

        # --- PASO C: Lógica de Creación/Actualización/Cierre ---

        # Buscar si ya hay CUALQUIER alerta abierta para este sitio
        alerta_existente = db.query(models.Alerta).filter(
            models.Alerta.id_sitio == sitio_con_relaciones.id_sitio,
            models.Alerta.estado_alerta == EstadoAlertaEnum.ABIERTA
        ).first()

        if tipo_alerta:
            # (Se necesita una alerta de tipo CRITICA o ADVERTENCIA)
            print(f"-> Tipo de alerta determinado: {tipo_alerta.value}")

            if alerta_existente:
                if alerta_existente.tipo_alerta == tipo_alerta:
                    # CASO 1: Alerta existente es del MISMO tipo -> ACTUALIZAR
                    print(f"-> Actualizando alerta existente ID {alerta_existente.id_alerta} con nuevo mensaje.")
                    alerta_existente.mensaje = mensaje
                    alerta_existente.id_prediccion = prediccion_actualizada.id_prediccion
                    alerta_existente.actualizado_en = datetime.now()
                    db.add(alerta_existente)
                    db.commit()
                    alertas_actualizadas += 1
                    # (Opcional: enviar correo de actualización si el mensaje cambió mucho)

                else:
                    # CASO 2: Alerta existente es de DIFERENTE tipo -> CERRAR LA VIEJA y CREAR NUEVA
                    print(
                        f"-> Cerrando alerta vieja ID {alerta_existente.id_alerta} (tipo {alerta_existente.tipo_alerta.value})...")
                    alerta_crud.close_alert(db, db_alerta=alerta_existente)

                    # (Lógica de crear nueva)
                    print("-> Creando nueva alerta...")
                    alerta_data = alerta_schema.AlertaCreate(
                        id_sitio=sitio_con_relaciones.id_sitio,
                        id_prediccion=prediccion_actualizada.id_prediccion,
                        tipo_alerta=tipo_alerta,
                        mensaje=mensaje
                    )
                    nueva_alerta = alerta_crud.create_alerta(db, alerta=alerta_data)
                    nuevas_alertas_generadas += 1
                    await notificar_alerta(db, nueva_alerta, sitio_con_relaciones)  # Enviar correo

            else:
                # CASO 3: No hay alerta existente -> CREAR NUEVA
                print("-> Creando nueva alerta...")
                alerta_data = alerta_schema.AlertaCreate(
                    id_sitio=sitio_con_relaciones.id_sitio,
                    id_prediccion=prediccion_actualizada.id_prediccion,
                    tipo_alerta=tipo_alerta,
                    mensaje=mensaje
                )
                nueva_alerta = alerta_crud.create_alerta(db, alerta=alerta_data)
                nuevas_alertas_generadas += 1
                await notificar_alerta(db, nueva_alerta, sitio_con_relaciones)  # Enviar correo

        else:
            # (No se necesita alerta nueva, días restantes > 14)
            print("-> Días restantes suficientes. No se requiere alerta nueva.")
            if alerta_existente:
                # CASO 4: Ya no se necesita alerta, pero hay una abierta -> CERRARLA
                print(
                    f"-> Cerrando alerta obsoleta ID {alerta_existente.id_alerta} (tipo {alerta_existente.tipo_alerta.value}).")
                alerta_crud.close_alert(db, db_alerta=alerta_existente)

    print(
        f"--- Fin generación. Nuevas alertas creadas: {nuevas_alertas_generadas}. Alertas actualizadas: {alertas_actualizadas} ---")
    return {
        "mensaje": f"Proceso completado. {nuevas_alertas_generadas} nuevas alertas creadas, {alertas_actualizadas} actualizadas."}


# --- Función Auxiliar para Enviar Correo ---
# (La movimos aquí para no repetir código)
async def notificar_alerta(db: Session, nueva_alerta: models.Alerta, sitio_con_relaciones: models.Sitio):
    """Función interna para manejar el envío de correo y el logging."""
    if (sitio_con_relaciones.tecnico and
            sitio_con_relaciones.tecnico.usuario and
            sitio_con_relaciones.tecnico.usuario.correo):

        id_usuario_destino = sitio_con_relaciones.tecnico.id_usuario
        email_destino = sitio_con_relaciones.tecnico.usuario.correo
        nombre_tecnico = sitio_con_relaciones.tecnico.nombre_tecnico
        nombre_sitio = sitio_con_relaciones.nombre

        try:
            print(f"-> Intentando enviar correo de alerta a: {email_destino}")
            await email_service.send_new_alert_notification(
                db=db,
                user_id=id_usuario_destino,
                alerta_id=nueva_alerta.id_alerta,
                email_to=email_destino,
                nombre_tecnico=nombre_tecnico,
                nombre_sitio=nombre_sitio,
                tipo_alerta=nueva_alerta.tipo_alerta.value,
                mensaje_alerta=nueva_alerta.mensaje
            )
            print(f"-> Llamada a send_new_alert_notification completada.")

        except Exception as e:
            print(
                f"!!!!!!!! ERROR durante la llamada a send_new_alert_notification para alerta ID {nueva_alerta.id_alerta} !!!!!!!!")
            print(f"Error: {e}")
            print(traceback.format_exc())
            # El log de fallo ya lo maneja email_service, así que solo imprimimos.

    else:
        print("-> No se encontró información completa del técnico/usuario asignado al sitio para enviar correo.")