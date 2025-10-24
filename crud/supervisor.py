from sqlalchemy.orm import Session, joinedload
from db import models

def get_supervisores(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Supervisor).options(
        joinedload(models.Supervisor.contratista)
    ).order_by(models.Supervisor.nombre_completo).offset(skip).limit(limit).all()