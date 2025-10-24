from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from db.models import AbastecimientoStatus

# --- Schema específico para mostrar info del sitio en el historial ---
class SitioParaHistorial(BaseModel):
    id: str
    nombre: str

    class Config:
        from_attributes = True

# --- Schema para la respuesta del endpoint de historial ---
class AbastecimientoHistorial(BaseModel):
    id_abastecimiento: int
    ot: str
    fecha: datetime
    gls_existentes: float
    gls_abastecidos: float
    horometraje: float
    rendimiento_mg: Optional[float] = None
    alarma_transferencia: bool
    alarma_falla_energia: bool
    status: AbastecimientoStatus
    sitio: Optional[SitioParaHistorial] = None

    class Config:
        from_attributes = True

# --- Schemas existentes (modificados para consistencia) ---
class AbastecimientoBase(BaseModel):
    ot: str
    fecha: datetime
    gls_existentes: float
    gls_abastecidos: float
    horometraje: float
    rendimiento_mg: Optional[float] = None
    alarma_transferencia: bool = False
    alarma_falla_energia: bool = False

class AbastecimientoCreate(AbastecimientoBase):
    id_sitio: int
    id_tipo_sitio: int

class Abastecimiento(AbastecimientoBase):
    id_abastecimiento: int
    status: AbastecimientoStatus
    # Usamos SitioParaHistorial para ser consistentes
    sitio: Optional[SitioParaHistorial] = None

    class Config:
        from_attributes = True

class AbastecimientoUpdate(BaseModel):
    ot: Optional[str] = None
    gls_existentes: Optional[float] = None
    gls_abastecidos: Optional[float] = None
    horometraje: Optional[float] = None
    rendimiento_mg: Optional[float] = None
    alarma_transferencia: Optional[bool] = None
    alarma_falla_energia: Optional[bool] = None