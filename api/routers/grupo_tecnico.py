# api/routers/grupo_tecnico.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from schemas import grupo_tecnico as grupo_tecnico_schema
from crud import grupo_tecnico as grupo_tecnico_crud
from api import deps
from db import models

router = APIRouter(
    prefix="/grupos_tecnico",
    tags=["Grupos de Técnicos"]
)

@router.get("/", response_model=List[grupo_tecnico_schema.GrupoTecnico])
def read_grupos_tecnico(
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    return grupo_tecnico_crud.get_grupos_tecnico(db)