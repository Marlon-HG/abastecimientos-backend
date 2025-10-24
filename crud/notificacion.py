# crud/notificacion.py
from sqlalchemy.orm import Session, joinedload
from db import models
from schemas import notificacion as notificacion_schema

def create_log(db: Session, log: notificacion_schema.NotificacionLogCreate):
    """
    Crea un nuevo registro en el log de notificaciones.
    """
    db_log = models.NotificacionLog(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# --- NUEVAS FUNCIONES PARA LA CONFIGURACIÓN ---

def get_config_by_id(db: Session, config_id: int):
    return db.query(models.NotificacionConfiguracion).filter(models.NotificacionConfiguracion.id_configuracion == config_id).first()

def get_config_by_details(db: Session, config: notificacion_schema.NotificacionConfigCreate):
    """Busca si ya existe una configuración con los mismos detalles para evitar duplicados."""
    return db.query(models.NotificacionConfiguracion).filter(
        models.NotificacionConfiguracion.id_usuario == config.id_usuario,
        models.NotificacionConfiguracion.tipo_alerta == config.tipo_alerta,
        models.NotificacionConfiguracion.canal_envio == config.canal_envio
    ).first()

def get_all_configs(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene todas las configuraciones con detalles del usuario."""
    return db.query(models.NotificacionConfiguracion).options(
        joinedload(models.NotificacionConfiguracion.usuario)
    ).offset(skip).limit(limit).all()

def create_config(db: Session, config: notificacion_schema.NotificacionConfigCreate):
    """Crea una nueva regla de configuración de notificación."""
    db_config = models.NotificacionConfiguracion(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def update_config(db: Session, db_config: models.NotificacionConfiguracion, config_update: notificacion_schema.NotificacionConfigUpdate):
    """Actualiza una regla de configuración (ej. para activar/desactivar)."""
    db_config.activado = config_update.activado
    db.commit()
    db.refresh(db_config)
    return db_config

def delete_config(db: Session, config_id: int):
    """Elimina una regla de configuración."""
    db_config = db.query(models.NotificacionConfiguracion).filter(models.NotificacionConfiguracion.id_configuracion == config_id).first()
    if db_config:
        db.delete(db_config)
        db.commit()
    return db_config