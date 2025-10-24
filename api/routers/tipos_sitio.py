from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from schemas import tipo_sitio as tipo_sitio_schema
from crud import tipo_sitio as tipo_sitio_crud
from api import deps

router = APIRouter(prefix="/tipos_sitio", tags=["Tipos de Sitio"])

@router.get("/", response_model=List[tipo_sitio_schema.TipoSitio])
def read_tipos_sitio(db: Session = Depends(deps.get_db), current_user = Depends(deps.get_current_user)):
    return tipo_sitio_crud.get_tipos_sitio(db)