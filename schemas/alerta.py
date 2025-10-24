from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from db.models import TipoAlertaEnum, EstadoAlertaEnum # Enums de DB

# Importar el schema Prediccion (ya corregido)
from .prediccion import Prediccion as PrediccionSchema

# Importar el schema 'SitioSimple'
from .sitio import SitioSimple as SitioSchema # Usar SitioSimple para anidar

# Schema base para Alerta
class AlertaBase(BaseModel):
    id_sitio: int
    id_prediccion: Optional[int] = None
    tipo_alerta: TipoAlertaEnum
    mensaje: str

# Schema para crear una Alerta
class AlertaCreate(AlertaBase):
    pass

# Schema para leer/devolver una Alerta desde la API
class Alerta(AlertaBase):
    id_alerta: int
    estado_alerta: EstadoAlertaEnum
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema extendido que incluye detalles
class AlertaDetails(Alerta):
    # Usar el schema SitioSchema (que ahora es SitioSimple)
    sitio: Optional[SitioSchema] = None
    prediccion: Optional[PrediccionSchema] = None

    class Config:
        from_attributes = True