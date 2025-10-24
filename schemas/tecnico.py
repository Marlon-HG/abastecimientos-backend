from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from . import grupo_tecnico as grupo_tecnico_schema
from . import contratista as contratista_schema # <-- 1. Importa el schema de contratista

# Schema base con los campos comunes
class TecnicoBase(BaseModel):
    nombre_tecnico: str
    dpi_tecnico: str
    correo_tecnico: EmailStr
    cel_tecnico_contrata: Optional[str] = None
    cel_tecnico_personal: Optional[str] = None
    fec_nac_tecnico: Optional[date] = None
    id_grupo: Optional[int] = None
    id_contratista: Optional[int] = None
    status: bool = True

# Schema para la creación de un técnico
class TecnicoCreate(TecnicoBase):
    nombre_completo_usuario: str
    contrasena_usuario: str

# Schema para la actualización
class TecnicoUpdate(BaseModel):
    nombre_tecnico: Optional[str] = None
    dpi_tecnico: Optional[str] = None
    correo_tecnico: Optional[EmailStr] = None
    cel_tecnico_contrata: Optional[str] = None
    cel_tecnico_personal: Optional[str] = None
    fec_nac_tecnico: Optional[date] = None
    id_grupo: Optional[int] = None
    id_contratista: Optional[int] = None
    status: Optional[bool] = None

# Schema para la lectura (lo que devuelve la API)
class Tecnico(TecnicoBase):
    id_tecnico: int
    id_usuario: int
    grupo_tecnico: Optional[grupo_tecnico_schema.GrupoTecnico] = None
    # --- 2. CORRECCIÓN AQUÍ ---
    # Añade la propiedad para anidar la información del contratista
    contratista: Optional[contratista_schema.Contratista] = None

    class Config:
        from_attributes = True