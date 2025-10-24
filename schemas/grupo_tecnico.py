# schemas/grupo_tecnico.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GrupoTecnicoBase(BaseModel):
    codigo: str
    nombre: str
    activo: bool = True

class GrupoTecnicoCreate(GrupoTecnicoBase):
    pass

class GrupoTecnico(GrupoTecnicoBase):
    id_grupo: int
    creado_en: datetime
    actualizado_en: datetime

    class Config:
        from_attributes = True