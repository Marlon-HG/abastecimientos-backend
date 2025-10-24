# api/routers/roles.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from db import models
from api import deps

# Usaremos el schema de Rol que ya creamos en schemas/usuario.py
from schemas.usuario import Rol as RolSchema

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=List[RolSchema])
def get_all_roles(
    db: Session = Depends(deps.get_db),
    # Protegemos la ruta para que solo un admin pueda ver los roles
    current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    """
    Obtiene una lista de todos los roles disponibles en el sistema.
    """
    return db.query(models.Rol).all()