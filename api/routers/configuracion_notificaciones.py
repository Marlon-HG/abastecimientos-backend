# api/routers/configuracion_notificaciones.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api import deps
from crud import notificacion as notificacion_crud
from crud import usuario as usuario_crud
from db import models
from schemas import notificacion as notificacion_schema

router = APIRouter(
    prefix="/configuracion-notificaciones",
    tags=["Configuración de Notificaciones"]
)

@router.post("/", response_model=notificacion_schema.NotificacionConfig, status_code=status.HTTP_201_CREATED)
def create_notification_config(
    config_in: notificacion_schema.NotificacionConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    """
    Crea una nueva regla de notificación. (Solo Admins)
    """
    # Verificar que el usuario al que se le asigna la regla exista
    user = usuario_crud.get_user_by_id(db, user_id=config_in.id_usuario)
    if not user:
        raise HTTPException(status_code=404, detail="El usuario especificado no existe.")

    # Verificar que la regla no exista ya
    existing_config = notificacion_crud.get_config_by_details(db, config=config_in)
    if existing_config:
        raise HTTPException(status_code=400, detail="Ya existe una regla idéntica.")

    return notificacion_crud.create_config(db, config=config_in)

@router.get("/", response_model=List[notificacion_schema.NotificacionConfigDetails])
def read_all_notification_configs(
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    """
    Obtiene una lista de todas las reglas de notificación. (Solo Admins)
    """
    return notificacion_crud.get_all_configs(db)

@router.put("/{config_id}", response_model=notificacion_schema.NotificacionConfig)
def update_notification_config(
    config_id: int,
    config_in: notificacion_schema.NotificacionConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    """
    Actualiza una regla de notificación (activar/desactivar). (Solo Admins)
    """
    db_config = notificacion_crud.get_config_by_id(db, config_id=config_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada.")

    return notificacion_crud.update_config(db, db_config=db_config, config_update=config_in)

@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    """
    Elimina una regla de notificación. (Solo Admins)
    """
    db_config = notificacion_crud.get_config_by_id(db, config_id=config_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada.")

    notificacion_crud.delete_config(db, config_id=config_id)
    return None