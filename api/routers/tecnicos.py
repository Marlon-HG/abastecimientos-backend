from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# --- 1. AÑADE/VERIFICA ESTAS IMPORTACIONES ---
from schemas import tecnico as tecnico_schema, sitio as sitio_schema
from crud import tecnico as tecnico_crud
from api import deps
from db import models

router = APIRouter(
    prefix="/tecnicos",
    tags=["Técnicos"]
)


@router.get("/", response_model=List[tecnico_schema.Tecnico])
def read_all_tecnicos(
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    return tecnico_crud.get_tecnicos(db)


@router.post("/", response_model=tecnico_schema.Tecnico, status_code=status.HTTP_201_CREATED)
def create_new_tecnico(
        tecnico_data: tecnico_schema.TecnicoCreate,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    return tecnico_crud.create_tecnico(db=db, tecnico=tecnico_data)


@router.put("/{tecnico_id}", response_model=tecnico_schema.Tecnico)
def update_tecnico_by_id(
        tecnico_id: int,
        tecnico_data: tecnico_schema.TecnicoUpdate,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    updated_tecnico = tecnico_crud.update_tecnico(db, tecnico_id=tecnico_id, tecnico_update=tecnico_data)
    if not updated_tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Técnico con id {tecnico_id} no encontrado."
        )
    return updated_tecnico


@router.delete("/{tecnico_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tecnico_by_id(
        tecnico_id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    deleted_tecnico = tecnico_crud.delete_tecnico(db, tecnico_id=tecnico_id)
    if not deleted_tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Técnico con id {tecnico_id} no encontrado."
        )
    return


# --- 2. AÑADE ESTE NUEVO ENDPOINT AL FINAL ---
@router.get("/me/sitios", response_model=List[sitio_schema.Sitio])
def read_mis_sitios(
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_user)
):
    """
    Devuelve la lista de sitios asignados al técnico que está autenticado.
    Este endpoint es seguro y accesible para el rol de técnico.
    """
    # Verifica que el usuario actual tenga un perfil de técnico.
    # Gracias a la corrección de 'crud/usuario.py', current_user.tecnico ya vendrá cargado.
    if not current_user.tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario actual no es un técnico o no tiene un perfil asociado."
        )

    # Devuelve los sitios a través de la relación
    return current_user.tecnico.sitios