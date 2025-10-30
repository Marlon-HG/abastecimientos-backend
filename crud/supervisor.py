# C:\Users\marlo\Desktop\abastecimientos_backend\crud\supervisor.py
from sqlalchemy.orm import Session, joinedload
from db import models
from schemas import supervisor as supervisor_schema


# --- GET Múltiples (Sin cambios) ---
def get_supervisores(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Supervisor).options(
        joinedload(models.Supervisor.contratista)
    ).order_by(models.Supervisor.nombre_completo).offset(skip).limit(limit).all()


# --- GET por ID (Sin cambios) ---
def get_supervisor(db: Session, supervisor_id: int):
    return db.query(models.Supervisor).options(
        joinedload(models.Supervisor.contratista)
    ).filter(models.Supervisor.id_supervisor == supervisor_id).first()


# --- POST (Corregido) ---
def create_supervisor(db: Session, supervisor: supervisor_schema.SupervisorCreate):
    # NOTA: Tu log muestra que 'activo: 1' se está enviando.
    # Asumo que tu modelo 'models.Supervisor' tiene un default=1 para 'activo'.
    # Si no, tendrás que añadir 'activo=True' (o 1) aquí también.
    db_supervisor = models.Supervisor(
        nombre_completo=supervisor.nombre_completo,
        correo=supervisor.correo,
        telefono=supervisor.telefono,  # <-- AÑADIDO
        id_contratista=supervisor.id_contratista
    )
    db.add(db_supervisor)
    db.commit()
    db.refresh(db_supervisor)
    return db_supervisor


# --- PUT (Sin cambios) ---
# Esta función ya funciona bien, tomará 'telefono' si viene en el Update
def update_supervisor(db: Session, supervisor_id: int, supervisor: supervisor_schema.SupervisorUpdate):
    db_supervisor = get_supervisor(db, supervisor_id=supervisor_id)
    if not db_supervisor:
        return None

    update_data = supervisor.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_supervisor, key, value)

    db.commit()
    db.refresh(db_supervisor)
    return db_supervisor


# --- DELETE (Sin cambios) ---
def delete_supervisor(db: Session, supervisor_id: int):
    db_supervisor = get_supervisor(db, supervisor_id=supervisor_id)
    if not db_supervisor:
        return None
    db.delete(db_supervisor)
    db.commit()
    return db_supervisor