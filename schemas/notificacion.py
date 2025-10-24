#schemas/notificacion.py
from pydantic import BaseModel
from datetime import datetime
from db.models import TipoAlertaNotificacionEnum, CanalEnvioEnum, EstadoEnvioEnum # <-- Nombres corregidos
from .usuario import UsuarioSimple

# Schema para la configuración
class NotificacionConfiguracion(BaseModel):
    id_configuracion: int
    id_usuario: int
    tipo_alerta: TipoAlertaNotificacionEnum
    canal_envio: CanalEnvioEnum
    activado: bool

    class Config:
        from_attributes = True

# Schema para el log
class NotificacionLog(BaseModel):
    id_notificacion: int
    id_alerta: int | None = None
    id_abastecimiento: int | None = None
    id_usuario_destino: int
    canal_envio: CanalEnvioEnum
    estado_envio: EstadoEnvioEnum
    creado_en: datetime

    class Config:
        from_attributes = True

class NotificacionLogCreate(BaseModel):
    id_usuario_destino: int
    canal_envio: CanalEnvioEnum
    direccion_destino: str
    estado_envio: EstadoEnvioEnum
    id_alerta: int | None = None
    id_abastecimiento: int | None = None
    respuesta_proveedor: str | None = None

class NotificacionConfigBase(BaseModel):
    id_usuario: int
    tipo_alerta: TipoAlertaNotificacionEnum
    canal_envio: CanalEnvioEnum
    activado: bool = True

class NotificacionConfigCreate(NotificacionConfigBase):
    pass

class NotificacionConfigUpdate(BaseModel):
    activado: bool

class NotificacionConfig(NotificacionConfigBase):
    id_configuracion: int
    actualizado_en: datetime

    class Config:
        from_attributes = True

class NotificacionConfigDetails(NotificacionConfig):
    usuario: UsuarioSimple