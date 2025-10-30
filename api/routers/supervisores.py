# C:\Users\marlo\Desktop\abastecimientos_backend\api\routers\supervisores.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api import deps
from db import models
from crud import supervisor as supervisor_crud
from schemas import supervisor as supervisor_schema

router = APIRouter(prefix="/supervisores", tags=["Supervisores"])


# --- GET / (El que ya tenías) ---
@router.get("/", response_model=List[supervisor_schema.Supervisor])
def read_supervisores(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(deps.get_db),
        admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    supervisores = supervisor_crud.get_supervisores(db, skip=skip, limit=limit)
    return supervisores


# --- GET /{id} (Recomendado) ---
@router.get("/{supervisor_id}", response_model=supervisor_schema.Supervisor)
def read_supervisor(
        supervisor_id: int,
        db: Session = Depends(deps.get_db),
        admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    db_supervisor = supervisor_crud.get_supervisor(db, supervisor_id=supervisor_id)
    if db_supervisor is None:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    return db_supervisor


# --- POST / (Nuevo) ---
@router.post("/", response_model=supervisor_schema.Supervisor, status_code=status.HTTP_201_CREATED)
def create_supervisor(
        supervisor: supervisor_schema.SupervisorCreate,
        db: Session = Depends(deps.get_db),
        admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    # Opcional: Verificar si el correo ya existe
    db_user = db.query(models.Supervisor).filter(models.Supervisor.correo == supervisor.correo).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    return supervisor_crud.create_supervisor(db=db, supervisor=supervisor)


# --- PUT /{id} (Nuevo) ---
@router.put("/{supervisor_id}", response_model=supervisor_schema.Supervisor)
def update_supervisor(
        supervisor_id: int,
        supervisor: supervisor_schema.SupervisorUpdate,
        db: Session = Depends(deps.get_db),
        admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    db_supervisor = supervisor_crud.update_supervisor(db, supervisor_id=supervisor_id, supervisor=supervisor)
    if db_supervisor is None:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    return db_supervisor


# --- DELETE /{id} (Nuevo) ---
@router.delete("/{supervisor_id}", response_model=supervisor_schema.Supervisor)
def delete_supervisor(
        supervisor_id: int,
        db: Session = Depends(deps.get_db),
        admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    db_supervisor = supervisor_crud.delete_supervisor(db, supervisor_id=supervisor_id)
    if db_supervisor is None:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    return db_supervisor