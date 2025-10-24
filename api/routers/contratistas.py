# api/routers/contratistas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from schemas import contratista as contratista_schema
from crud import contratista as contratista_crud
from api import deps
from db import models

router = APIRouter(
    prefix="/contratistas",
    tags=["Contratistas"]
)

@router.get("/", response_model=List[contratista_schema.Contratista])
def read_all_contratistas(db: Session = Depends(deps.get_db), current_user: models.Usuario = Depends(deps.get_current_admin_user)):
    return contratista_crud.get_contratistas(db)

@router.post("/", response_model=contratista_schema.Contratista, status_code=status.HTTP_201_CREATED)
def create_new_contratista(contratista_data: contratista_schema.ContratistaCreate, db: Session = Depends(deps.get_db), current_user: models.Usuario = Depends(deps.get_current_admin_user)):
    return contratista_crud.create_contratista(db, contratista=contratista_data)

@router.put("/{contratista_id}", response_model=contratista_schema.Contratista)
def update_contratista_by_id(contratista_id: int, contratista_data: contratista_schema.ContratistaUpdate, db: Session = Depends(deps.get_db), current_user: models.Usuario = Depends(deps.get_current_admin_user)):
    updated_contratista = contratista_crud.update_contratista(db, contratista_id=contratista_id, contratista_update=contratista_data)
    if not updated_contratista:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contratista no encontrado")
    return updated_contratista

@router.delete("/{contratista_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contratista_by_id(contratista_id: int, db: Session = Depends(deps.get_db), current_user: models.Usuario = Depends(deps.get_current_admin_user)):
    deleted_contratista = contratista_crud.delete_contratista(db, contratista_id=contratista_id)
    if not deleted_contratista:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contratista no encontrado")
    return