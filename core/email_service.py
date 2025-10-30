from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from sqlalchemy.orm import Session
from core.config import settings
import datetime
from sqlalchemy.orm import Session

from db.models import CanalEnvioEnum
# --- CAMBIOS: Importar módulos para el logging ---
from db import models
from crud import notificacion as notificacion_crud
from schemas import notificacion as notificacion_schema

# --- CORRECCIÓN: Importar los Enums con el nombre correcto ---
from db.models import CanalEnvioEnum, EstadoEnvioEnum

conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_FROM,
    MAIL_PORT = settings.MAIL_PORT,
    MAIL_SERVER = settings.MAIL_SERVER,
    MAIL_STARTTLS = settings.MAIL_STARTTLS,
    MAIL_SSL_TLS = settings.MAIL_SSL_TLS,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


async def _send_and_log_message(db: Session, message: MessageSchema, log_data_dict: dict):
    """
    Función interna que intenta enviar un correo, añade el estado del envío al
    diccionario del log, y luego crea y guarda el registro.
    """
    from schemas.notificacion import MessageSchema, MessageType
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        # --- CORREGIDO ---
        log_data_dict['estado_envio'] = EstadoEnvioEnum.EXITOSO
    except Exception as e:
        # --- CORREGIDO ---
        log_data_dict['estado_envio'] = EstadoEnvioEnum.FALLIDO
        log_data_dict['respuesta_proveedor'] = str(e)[:255]
    finally:
        final_log = notificacion_schema.NotificacionLogCreate(**log_data_dict)
        notificacion_crud.create_log(db, log=final_log)


# --- CAMBIOS: Todas las funciones públicas ahora aceptan 'db' y contexto para el log ---

async def send_welcome_email(db: Session, user_id: int, email_to: str, nombre_usuario: str, contrasena: str):
    """
    Envía un correo de bienvenida a un nuevo usuario con sus credenciales.
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>¡Bienvenido a Bordo!</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dddddd; }}
            .header img {{ max-width: 150px; }}
            .content {{ padding: 20px 0; }}
            .content h1 {{ color: #333333; text-align: center; }}
            .content p {{ color: #555555; line-height: 1.6; }}
            .credentials {{ background-color: #f9f9f9; border-left: 5px solid #0056b3; padding: 15px; margin: 20px 0; }}
            .credentials p {{ margin: 5px 0; }}
            .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #888888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/umg2025/logo.png" alt="Logo Tigo">
            </div>
            <div class="content">
                <h1>¡Bienvenido, {nombre_usuario}!</h1>
                <p>Tu cuenta en el portal de Abastecimientos TIGO ha sido creada exitosamente. A continuación encontrarás tus credenciales de acceso:</p>
                <div class="credentials">
                    <p><strong>Usuario:</strong> {email_to}</p>
                    <p><strong>Contraseña:</strong> {contrasena}</p>
                </div>
                <p>Te recomendamos cambiar tu contraseña después de tu primer inicio de sesión por motivos de seguridad.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.date.today().year} Tigo Guatemala. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="Bienvenido al Portal de Abastecimientos TIGO",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )
    log_data_dict = {
        "id_usuario_destino": user_id,
        # --- CORREGIDO ---
        "canal_envio": CanalEnvioEnum.EMAIL,
        "direccion_destino": email_to
    }
    await _send_and_log_message(db, message, log_data_dict)


async def send_password_changed_notification_email(db: Session, user_id: int, email_to: str, nombre_usuario: str):
    """
    Envía una notificación al usuario informando que su contraseña ha sido cambiada.
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirmación de Cambio de Contraseña</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dddddd; }}
            .header img {{ max-width: 150px; }}
            .content {{ padding: 20px 0; }}
            .content h1 {{ color: #333333; text-align: center; }}
            .content p {{ color: #555555; line-height: 1.6; }}
            .alert {{ background-color: #fff3cd; border-left: 5px solid #ffeeba; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #888888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/umg2025/logo.png" alt="Logo Tigo">
            </div>
            <div class="content">
                <h1>Notificación de Seguridad</h1>
                <p>Hola {nombre_usuario},</p>
                <p>Te informamos que la contraseña de tu cuenta en el portal de Abastecimientos TIGO ha sido cambiada exitosamente.</p>
                <div class="alert">
                    <p><strong>Si no reconoces esta actividad, por favor contacta inmediatamente al administrador para asegurar tu cuenta.</strong></p>
                    <p>
                        Marlon Hernández<br>
                        marlon.hernandezgiron01@gmail.com<br>
                        +502 5015-1603
                    </p>
                </div>
            </div>
            <div class="footer">
                <p>&copy; {datetime.date.today().year} Tigo Guatemala. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="[Alerta de Seguridad] Tu contraseña ha sido cambiada",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )
    log_data_dict = {
        "id_usuario_destino": user_id,
        # --- CORREGIDO ---
        "canal_envio": CanalEnvioEnum.EMAIL,
        "direccion_destino": email_to
    }
    await _send_and_log_message(db, message, log_data_dict)


async def send_password_reset_email(db: Session, user_id: int, email_to: str, nombre_usuario: str, token: str):
    """
    Envía un correo con el enlace para restablecer la contraseña.
    """

    reset_url = f"https://abastecimientos-frontend.vercel.app/reset-password/{token}"

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Restablecimiento de Contraseña</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dddddd; }}
            .header img {{ max-width: 150px; }}
            .content {{ padding: 20px 0; }}
            .content h1 {{ color: #333333; text-align: center; }}
            .content p {{ color: #555555; line-height: 1.6; }}
            .button-container {{ text-align: center; padding: 20px 0; }}
            .button {{ background-color: #0056b3; color: #ffffff; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #888888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/umg2025/logo.png" alt="Logo Tigo">
            </div>
            <div class="content">
                <h1>Solicitud de Restablecimiento de Contraseña</h1>
                <p>Hola {nombre_usuario},</p>
                <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Si no has sido tú, puedes ignorar este correo de forma segura.</p>
                <p>Para continuar, por favor haz clic en el siguiente botón:</p>
                <div class="button-container">
                    <a href="{reset_url}" class="button" style="color: #ffffff;">Restablecer mi Contraseña</a>
                </div>
                <p>Este enlace es válido por 1 hora.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.date.today().year} Tigo Guatemala. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="Restablecimiento de Contraseña - Abastecimientos TIGO",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )
    log_data_dict = {
        "id_usuario_destino": user_id,
        "canal_envio": CanalEnvioEnum.EMAIL,
        "direccion_destino": email_to
    }
    await _send_and_log_message(db, message, log_data_dict)


async def send_abastecimiento_update_notification(
    db: Session,
    abastecimiento_id: int,
    recipients_map: dict, # Ej: {15: "correo1@example.com", 20: "correo2@example.com"}
    nombre_modificador: str,
    modificador_email: str,
    nombre_sitio: str,
    sitio_id: int,
    fecha_modificacion: str,
    changes_html: str
):
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notificación de Actualización de Registro</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dddddd; }}
            .header img {{ max-width: 150px; }}
            .content {{ padding: 20px 0; }}
            .content h1 {{ color: #333333; text-align: center; }}
            .content p {{ color: #555555; line-height: 1.6; }}
            .info-box {{ background-color: #f9f9f9; border-left: 5px solid #0056b3; padding: 1px 20px; margin: 20px 0; }}
            .changes-list {{ list-style-type: none; padding-left: 0; }}
            .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #888888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/umg2025/logo.png" alt="Logo Tigo">
            </div>
            <div class="content">
                <h1>Alerta de Modificación de Datos</h1>
                <p>Se ha realizado una actualización en un registro de abastecimiento.</p>
                <div class="info-box">
                    <h3>Detalles de la Modificación</h3>
                    <p><strong>Sitio:</strong> {nombre_sitio} (ID: {sitio_id})</p>
                    <p><strong>ID del Registro:</strong> {abastecimiento_id}</p>
                    <p><strong>Fecha del Cambio:</strong> {fecha_modificacion}</p>
                    <p><strong>Modificado por:</strong> {nombre_modificador} ({modificador_email})</p>
                </div>
                <div class="info-box">
                    <h3>Resumen de Cambios</h3>
                    <ul class="changes-list">
                        {changes_html}
                    </ul>
                </div>
                <p>Si tienes alguna pregunta, por favor contacta al usuario que realizó la modificación.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.date.today().year} Tigo Guatemala. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    for user_id, email_to in recipients_map.items():
        message = MessageSchema(
            subject=f"[Alerta] Modificación en Registro de Abastecimiento del Sitio {nombre_sitio}",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html
        )
        log_data_dict = {
            "id_usuario_destino": user_id,
            "id_abastecimiento": abastecimiento_id,
            # --- CORREGIDO ---
            "canal_envio": CanalEnvioEnum.EMAIL,
            "direccion_destino": email_to
        }
        await _send_and_log_message(db, message, log_data_dict)


async def send_abastecimiento_cancellation_notification(
    db: Session,
    abastecimiento_id: int,
    recipients_map: dict,
    nombre_cancelador: str,
    nombre_sitio: str,
    fecha_cancelacion: str
):
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notificación de Cancelación de Registro</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dddddd; }}
            .header img {{ max-width: 150px; }}
            .content {{ padding: 20px 0; }}
            .content h1 {{ color: #d9534f; text-align: center; }}
            .content p {{ color: #555555; line-height: 1.6; }}
            .info-box {{ background-color: #f2dede; border-left: 5px solid #d9534f; padding: 1px 20px; margin: 20px 0; }}
            .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #888888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/umg2025/logo.png" alt="Logo Tigo">
            </div>
            <div class="content">
                <h1>Alerta de Cancelación de Registro</h1>
                <p>Te informamos que se ha <b>cancelado</b> un registro de abastecimiento que podría afectar los cálculos de predicción y los reportes.</p>
                <div class="info-box">
                    <h3>Detalles de la Cancelación</h3>
                    <p><strong>Sitio:</strong> {nombre_sitio}</p>
                    <p><strong>ID del Registro Cancelado:</strong> {abastecimiento_id}</p>
                    <p><strong>Fecha de Cancelación:</strong> {fecha_cancelacion}</p>
                    <p><strong>Acción realizada por:</strong> {nombre_cancelador}</p>
                </div>
                <p>Este registro ya no será considerado para futuras operaciones. Si crees que esto es un error, por favor contacta al usuario que realizó la acción o a un administrador.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.date.today().year} Tigo Guatemala. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    for user_id, email_to in recipients_map.items():
        message = MessageSchema(
            subject=f"[Alerta de Seguridad] Cancelación de Registro en Sitio {nombre_sitio}",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html
        )
        log_data_dict = {
            "id_usuario_destino": user_id,
            "id_abastecimiento": abastecimiento_id,
            # --- CORREGIDO ---
            "canal_envio": CanalEnvioEnum.EMAIL,
            "direccion_destino": email_to
        }
        await _send_and_log_message(db, message, log_data_dict)


async def send_new_alert_notification(
    db: Session,
    user_id: int,
    alerta_id: int,
    email_to: str,
    nombre_tecnico: str,
    nombre_sitio: str,
    tipo_alerta: str,
    mensaje_alerta: str
):
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Nueva Alerta Generada</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dddddd; }}
            .header img {{ max-width: 150px; }}
            .content h1 {{ color: #d9534f; }}
            .alert-box {{ background-color: #f2dede; border-left: 5px solid #d9534f; padding: 1px 20px; margin: 20px 0; }}
            .footer {{ text-align: center; font-size: 12px; color: #888888; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/umg2025/logo.png" alt="Logo Tigo">
            </div>
            <div class="content">
                <h1>Alerta de Mantenimiento Requerido</h1>
                <p>Hola {nombre_tecnico},</p>
                <p>Se ha generado una nueva alerta automática que requiere tu atención en el siguiente sitio:</p>
                <div class="alert-box">
                    <h3>Detalles de la Alerta</h3>
                    <p><strong>Sitio:</strong> {nombre_sitio}</p>
                    <p><strong>Tipo de Alerta:</strong> {tipo_alerta}</p>
                    <p><strong>Mensaje:</strong> {mensaje_alerta}</p>
                </div>
                <p>Por favor, toma las acciones necesarias para atender esta alerta. Gracias.</p>
            </div>
            <div class="footer">
                <p>Este es un correo generado automáticamente.</p>
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject=f"[ALERTA] Acción Requerida en Sitio {nombre_sitio}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )
    log_data_dict = {
        "id_usuario_destino": user_id,
        "id_alerta": alerta_id,
        # --- CORREGIDO ---
        "canal_envio": CanalEnvioEnum.EMAIL,
        "direccion_destino": email_to
    }
    await _send_and_log_message(db, message, log_data_dict)


async def send_alert_resolved_notification(
    db: Session,
    alerta_id: int,
    recipients_map: dict,
    nombre_resolutor: str,
    nombre_sitio: str,
    mensaje_alerta: str
):
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Alerta Resuelta</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dddddd; }}
            .header img {{ max-width: 150px; }}
            .content h1 {{ color: #5cb85c; }}
            .resolved-box {{ background-color: #dff0d8; border-left: 5px solid #5cb85c; padding: 1px 20px; margin: 20px 0; }}
            .footer {{ text-align: center; font-size: 12px; color: #888888; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://storage.googleapis.com/umg2025/logo.png" alt="Logo Tigo">
            </div>
            <div class="content">
                <h1>Alerta Resuelta</h1>
                <p>Te informamos que una alerta ha sido marcada como resuelta.</p>
                <div class="resolved-box">
                    <h3>Detalles de la Resolución</h3>
                    <p><strong>Sitio:</strong> {nombre_sitio}</p>
                    <p><strong>ID de Alerta:</strong> {alerta_id}</p>
                    <p><strong>Alerta Original:</strong> "{mensaje_alerta}"</p>
                    <p><strong>Cerrada por:</strong> {nombre_resolutor}</p>
                </div>
                <p>No se requieren más acciones para esta alerta. Gracias por tu trabajo.</p>
            </div>
            <div class="footer">
                <p>Este es un correo generado automáticamente.</p>
            </div>
        </div>
    </body>
    </html>
    """
    for user_id, email_to in recipients_map.items():
        message = MessageSchema(
            subject=f"[RESUELTO] Alerta en Sitio {nombre_sitio}",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html
        )
        log_data_dict = {
            "id_usuario_destino": user_id,
            "id_alerta": alerta_id,
            # --- CORREGIDO ---
            "canal_envio": CanalEnvioEnum.EMAIL,
            "direccion_destino": email_to
        }
        await _send_and_log_message(db, message, log_data_dict)