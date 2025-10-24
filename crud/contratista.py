# crud/contratista.py
from sqlalchemy.orm import Session
from db import models
from schemas import contratista as contratista_schema


def get_contratistas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Contratista).order_by(models.Contratista.nombre_contrata).offset(skip).limit(limit).all()


def create_contratista(db: Session, contratista: contratista_schema.ContratistaCreate):
    db_contratista = models.Contratista(**contratista.model_dump())
    db.add(db_contratista)
    db.commit()
    db.refresh(db_contratista)
    return db_contratista


def update_contratista(db: Session, contratista_id: int, contratista_update: contratista_schema.ContratistaUpdate):
    db_contratista = db.query(models.Contratista).filter(models.Contratista.id_contratista == contratista_id).first()
    if not db_contratista:
        return None

    update_data = contratista_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_contratista, key, value)

    db.commit()
    db.refresh(db_contratista)
    return db_contratista


def delete_contratista(db: Session, contratista_id: int):
    db_contratista = db.query(models.Contratista).filter(models.Contratista.id_contratista == contratista_id).first()
    if not db_contratista:
        return None
    db.delete(db_contratista)
    db.commit()
    return db_contratista