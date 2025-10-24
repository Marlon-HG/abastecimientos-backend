from sqlalchemy.orm import Session, joinedload
from db import models
from schemas import sitio as sitio_schema
from fastapi import HTTPException


def get_sitios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sitio).options(
        joinedload(models.Sitio.tipo_sitio),
        joinedload(models.Sitio.supervisor),
        joinedload(models.Sitio.tecnico)
    ).order_by(models.Sitio.nombre).offset(skip).limit(limit).all()


def create_sitio(db: Session, sitio: sitio_schema.SitioCreate):
    db_sitio_check = db.query(models.Sitio).filter(models.Sitio.id == sitio.id).first()
    if db_sitio_check:
        raise HTTPException(status_code=400, detail=f"El ID de sitio '{sitio.id}' ya existe.")

    db_sitio = models.Sitio(**sitio.model_dump())
    db.add(db_sitio)
    db.commit()
    db.refresh(db_sitio)
    return db_sitio


def update_sitio(db: Session, sitio_id: int, sitio_update: sitio_schema.SitioUpdate):
    db_sitio = db.query(models.Sitio).filter(models.Sitio.id_sitio == sitio_id).first()
    if not db_sitio:
        return None

    update_data = sitio_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sitio, key, value)

    db.commit()
    db.refresh(db_sitio)
    return db_sitio


def delete_sitio(db: Session, sitio_id: int):
    db_sitio = db.query(models.Sitio).filter(models.Sitio.id_sitio == sitio_id).first()
    if not db_sitio:
        return None
    db.delete(db_sitio)
    db.commit()
    return db_sitio