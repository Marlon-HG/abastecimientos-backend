from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from schemas import sitio as sitio_schema
from crud import sitio as sitio_crud
from api import deps
from db import models

router = APIRouter(
    prefix="/sitios",
    tags=["Sitios"]
)

@router.get("/", response_model=List[sitio_schema.Sitio])
def read_sitios(
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_supervisor_or_admin_user)
):
    return sitio_crud.get_sitios(db)

@router.post("/", response_model=sitio_schema.Sitio, status_code=status.HTTP_201_CREATED)
def create_new_sitio(
    sitio_data: sitio_schema.SitioCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    return sitio_crud.create_sitio(db=db, sitio=sitio_data)

@router.put("/{sitio_id}", response_model=sitio_schema.Sitio)
def update_sitio_by_id(
    sitio_id: int,
    sitio_data: sitio_schema.SitioUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    updated_sitio = sitio_crud.update_sitio(db, sitio_id=sitio_id, sitio_update=sitio_data)
    if not updated_sitio:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sitio no encontrado")
    return updated_sitio

@router.delete("/{sitio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sitio_by_id(
    sitio_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    deleted_sitio = sitio_crud.delete_sitio(db, sitio_id=sitio_id)
    if not deleted_sitio:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sitio no encontrado")
    return