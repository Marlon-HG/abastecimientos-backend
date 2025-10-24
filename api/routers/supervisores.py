from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from api import deps
from db import models
from crud import supervisor as supervisor_crud
from schemas import supervisor as supervisor_schema

router = APIRouter(prefix="/supervisores", tags=["Supervisores"])

@router.get("/", response_model=List[supervisor_schema.Supervisor])
def read_supervisores(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    supervisores = supervisor_crud.get_supervisores(db, skip=skip, limit=limit)
    return supervisores