#schemas/supervisor.py
from pydantic import BaseModel
from typing import Optional

class ContratistaSimple(BaseModel):
    nombre_contrata: str
    class Config:
        from_attributes = True

class Supervisor(BaseModel):
    id_supervisor: int
    nombre_completo: str
    correo: str
    contratista: Optional[ContratistaSimple] = None

    class Config:
        from_attributes = True