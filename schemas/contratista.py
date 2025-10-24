# schemas/contratista.py
from pydantic import BaseModel
from typing import Optional

class ContratistaBase(BaseModel):
    nombre_contrata: str
    activo: bool = True

class ContratistaCreate(ContratistaBase):
    pass

class ContratistaUpdate(BaseModel):
    nombre_contrata: Optional[str] = None
    activo: Optional[bool] = None

class Contratista(ContratistaBase):
    id_contratista: int

    class Config:
        from_attributes = True