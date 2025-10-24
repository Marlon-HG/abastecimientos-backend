# crud/grupo_tecnico.py

from sqlalchemy.orm import Session
from db import models
from schemas import grupo_tecnico as grupo_tecnico_schema

def get_grupos_tecnico(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.GrupoTecnico).offset(skip).limit(limit).all()

def get_grupo_tecnico(db: Session, grupo_id: int):
    return db.query(models.GrupoTecnico).filter(models.GrupoTecnico.id_grupo == grupo_id).first()