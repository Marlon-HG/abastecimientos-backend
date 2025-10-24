from sqlalchemy.orm import Session, joinedload
from db import models
from schemas import alerta as alerta_schema
# --- Importa los Enums correctos ---
from db.models import EstadoAlertaEnum, TipoAlertaEnum

def create_alerta(db: Session, alerta: alerta_schema.AlertaCreate):
    """
    Crea una nueva alerta si no existe una abierta del mismo tipo para el mismo sitio.
    """
    existing_alert = db.query(models.Alerta).filter(
        models.Alerta.id_sitio == alerta.id_sitio,
        models.Alerta.tipo_alerta == alerta.tipo_alerta,
        # --- CORREGIDO ---
        models.Alerta.estado_alerta == EstadoAlertaEnum.ABIERTA
    ).first()

    if existing_alert:
        return existing_alert

    db_alerta = models.Alerta(
        id_sitio=alerta.id_sitio,
        id_prediccion=alerta.id_prediccion,
        tipo_alerta=alerta.tipo_alerta,
        mensaje=alerta.mensaje,
        # --- CORREGIDO ---
        estado_alerta=EstadoAlertaEnum.ABIERTA
    )
    db.add(db_alerta)
    db.commit()
    db.refresh(db_alerta)
    return db_alerta

def get_open_alerts(db: Session):
    """
    Recupera todas las alertas con estado 'ABIERTA'.
    """
    return db.query(models.Alerta).options(
        joinedload(models.Alerta.sitio),
        joinedload(models.Alerta.prediccion)
    ).filter(
        # --- CORREGIDO ---
        models.Alerta.estado_alerta == EstadoAlertaEnum.ABIERTA
    ).order_by(
        models.Alerta.creado_en.desc()
    ).all()

def get_alert_by_id(db: Session, alerta_id: int):
    """
    Recupera una alerta específica por su ID.
    """
    return db.query(models.Alerta).options(
        joinedload(models.Alerta.sitio).joinedload(models.Sitio.supervisor),
        joinedload(models.Alerta.sitio).joinedload(models.Sitio.tecnico).joinedload(models.Tecnico.usuario)
    ).filter(models.Alerta.id_alerta == alerta_id).first()


def close_alert(db: Session, db_alerta: models.Alerta):
    """
    Cambia el estado de una alerta a 'CERRADA'.
    """
    # --- CORREGIDO ---
    if db_alerta.estado_alerta == EstadoAlertaEnum.CERRADA:
        return db_alerta

    db_alerta.estado_alerta = EstadoAlertaEnum.CERRADA
    db.add(db_alerta)
    db.commit()
    db.refresh(db_alerta)
    return db_alerta