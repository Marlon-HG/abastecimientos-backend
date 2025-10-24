# db/models.py

import enum
from sqlalchemy import (Column, Integer, String, Boolean, TIMESTAMP, text,
                        ForeignKey, Float, DateTime, Table, Enum as SQLAlchemyEnum, Date)
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.sql import func # Necesario para server_default y onupdate

# --- TABLA DE ASOCIACIÓN USUARIO-ROL ---
usuario_rol = Table('usuario_rol', Base.metadata,
                    Column('id_usuario', Integer, ForeignKey('usuario.id_usuario', ondelete="CASCADE"), primary_key=True),
                    Column('id_rol', Integer, ForeignKey('rol.id_rol'), primary_key=True)
                    )

# --- ENUMS ESTANDARIZADOS DE PYTHON ---
class RolEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    TECNICO = "TECNICO"

class AbastecimientoStatus(str, enum.Enum):
    ACTIVO = "ACTIVO"
    CANCELADO = "CANCELADO"

class TipoAlertaEnum(str, enum.Enum):
    ADVERTENCIA = "ADVERTENCIA"
    CRITICA = "CRITICA"
    INFORMATIVA = "INFORMATIVA"

class EstadoAlertaEnum(str, enum.Enum):
    ABIERTA = "ABIERTA"
    ENVIADA = "ENVIADA"
    CERRADA = "CERRADA"

class TipoAlertaNotificacionEnum(str, enum.Enum):
    ADVERTENCIA = "ADVERTENCIA"
    CRITICA = "CRITICA"
    INFORMATIVA = "INFORMATIVA"
    REPORTE = "REPORTE"

class CanalEnvioEnum(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"

class EstadoEnvioEnum(str, enum.Enum):
    EXITOSO = "EXITOSO"
    FALLIDO = "FALLIDO"

# --- MODELOS DE LA BASE DE DATOS ---

class Rol(Base):
    __tablename__ = 'rol'
    id_rol = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(255))
    activo = Column(Boolean, default=True)
    usuarios = relationship("Usuario", secondary=usuario_rol, back_populates="roles")


class Usuario(Base):
    __tablename__ = 'usuario'
    id_usuario = Column(Integer, primary_key=True)
    nombre_completo = Column(String(120), nullable=False)
    contrasena = Column(String(255), nullable=False)
    correo = Column(String(160), unique=True, nullable=False, index=True)
    activo = Column(Boolean, default=True, nullable=False)
    reset_token = Column(String(255), unique=True, index=True, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # --- Relaciones ---
    roles = relationship("Rol", secondary=usuario_rol, back_populates="usuarios")
    tecnico = relationship("Tecnico", back_populates="usuario", uselist=False, cascade="all, delete-orphan")

    # --- CORRECCIÓN: Relación inversa a Supervisor ELIMINADA ---
    # supervisor = relationship("Supervisor", back_populates="usuario", uselist=False, cascade="all, delete-orphan") # Eliminada
    # --- FIN CORRECCIÓN ---

    notificaciones_config = relationship("NotificacionConfiguracion", back_populates="usuario", cascade="all, delete-orphan")
    notificaciones_recibidas = relationship("NotificacionLog", back_populates="usuario_destino", cascade="all, delete-orphan")


class Contratista(Base):
    __tablename__ = 'contratista'
    id_contratista = Column(Integer, primary_key=True)
    nombre_contrata = Column(String(50), nullable=False)
    activo = Column(Boolean, default=True)

    supervisores = relationship("Supervisor", back_populates="contratista")
    tecnicos = relationship("Tecnico", back_populates="contratista")
    sitios = relationship("Sitio", back_populates="contratista")


class Supervisor(Base):
    __tablename__ = 'supervisor'
    id_supervisor = Column(Integer, primary_key=True)
    nombre_completo = Column(String(120), nullable=False)
    correo = Column(String(160), nullable=False)
    telefono = Column(String(20))
    id_contratista = Column(Integer, ForeignKey('contratista.id_contratista'))

    # --- CORRECCIÓN: Columna y relación a Usuario ELIMINADAS ---
    # id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), unique=True, nullable=True) # Eliminada
    # usuario = relationship("Usuario", back_populates="supervisor") # Eliminada
    # --- FIN CORRECCIÓN ---

    activo = Column(Boolean, default=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Otras relaciones
    contratista = relationship("Contratista", back_populates="supervisores")
    sitios = relationship("Sitio", back_populates="supervisor")


class GrupoTecnico(Base):
    __tablename__ = 'grupo_tecnico'
    id_grupo = Column(Integer, primary_key=True)
    codigo = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(25), nullable=False)
    activo = Column(Boolean, default=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tecnicos = relationship("Tecnico", back_populates="grupo_tecnico")


class Tecnico(Base):
    __tablename__ = 'tecnico'
    id_tecnico = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), unique=True, nullable=False)
    id_grupo = Column(Integer, ForeignKey('grupo_tecnico.id_grupo'), nullable=False)
    nombre_tecnico = Column(String(120), nullable=False)
    dpi_tecnico = Column(String(13), unique=True, nullable=False)
    cel_tecnico_contrata = Column(String(20))
    cel_tecnico_personal = Column(String(20))
    fec_nac_tecnico = Column(Date)
    correo_tecnico = Column(String(160), unique=True, nullable=False)
    id_contratista = Column(Integer, ForeignKey('contratista.id_contratista'), nullable=False)
    status = Column(Boolean, default=True)

    # Relaciones
    usuario = relationship("Usuario", back_populates="tecnico")
    sitios = relationship("Sitio", back_populates="tecnico")
    grupo_tecnico = relationship("GrupoTecnico", back_populates="tecnicos")
    contratista = relationship("Contratista", back_populates="tecnicos")
    # abastecimientos = relationship("Abastecimiento", back_populates="tecnico") # Eliminado


class TipoSitio(Base):
    __tablename__ = 'tipo_sitio'
    id_tipo_sitio = Column(Integer, primary_key=True)
    nombre_tipo_sitio = Column(String(20), nullable=False)
    sitios = relationship("Sitio", back_populates="tipo_sitio")


class Sitio(Base):
    __tablename__ = 'sitio'
    id_sitio = Column(Integer, primary_key=True, index=True)
    id = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(160), index=True, nullable=False)
    departamento = Column(String(60), nullable=False)
    municipio = Column(String(60), nullable=False)
    id_tipo_sitio = Column(Integer, ForeignKey('tipo_sitio.id_tipo_sitio'))
    id_supervisor = Column(Integer, ForeignKey('supervisor.id_supervisor'))
    dir_detallada = Column(String(160))
    latitud = Column(String(50))
    longitud = Column(String(50))
    id_tecnico = Column(Integer, ForeignKey('tecnico.id_tecnico'))
    id_contratista = Column(Integer, ForeignKey('contratista.id_contratista'))

    # Relaciones
    tipo_sitio = relationship("TipoSitio", back_populates="sitios")
    tecnico = relationship("Tecnico", back_populates="sitios")
    supervisor = relationship("Supervisor", back_populates="sitios")
    contratista = relationship("Contratista", back_populates="sitios")
    prediccion = relationship("PrediccionAbastecimiento", uselist=False, back_populates="sitio")
    abastecimientos = relationship("Abastecimiento", back_populates="sitio", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="sitio", cascade="all, delete-orphan")


class Abastecimiento(Base):
    __tablename__ = 'abastecimiento'
    id_abastecimiento = Column(Integer, primary_key=True)
    id_sitio = Column(Integer, ForeignKey('sitio.id_sitio'))
    id_tipo_sitio = Column(Integer, ForeignKey('tipo_sitio.id_tipo_sitio'))
    # id_tecnico = Column(Integer, ForeignKey('tecnico.id_tecnico'), nullable=False) # Eliminado
    status = Column(String(20), nullable=False, default='ACTIVO')
    ot = Column(String(20), nullable=False)
    fecha = Column(DateTime, nullable=False)
    gls_existentes = Column(Float, nullable=False)
    gls_abastecidos = Column(Float, nullable=False)
    horometraje = Column(Float, nullable=False)
    rendimiento_mg = Column(Float, nullable=False)
    alarma_transferencia = Column(Boolean, default=False)
    alarma_falla_energia = Column(Boolean, default=False)

    # Relaciones
    sitio = relationship("Sitio", back_populates="abastecimientos")
    tipo_sitio_ref = relationship("TipoSitio")
    notificaciones_log = relationship("NotificacionLog", back_populates="abastecimiento")
    # tecnico = relationship("Tecnico", back_populates="abastecimientos") # Eliminado


class PrediccionAbastecimiento(Base):
    __tablename__ = 'prediccion_abastecimiento'
    id_prediccion = Column(Integer, primary_key=True, index=True)
    id_sitio = Column(Integer, ForeignKey('sitio.id_sitio'), nullable=False, unique=True)
    fecha_proximo_abastecimiento = Column(DateTime, nullable=False)
    id_ultimo_abastecimiento_usado = Column(Integer, ForeignKey('abastecimiento.id_abastecimiento'), nullable=False)
    horometro_estimado_fin = Column(Float, nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    # Relaciones
    sitio = relationship("Sitio", back_populates="prediccion")
    ultimo_abastecimiento = relationship("Abastecimiento")
    alertas = relationship("Alerta", back_populates="prediccion")


class Alerta(Base):
    __tablename__ = 'alerta'
    id_alerta = Column(Integer, primary_key=True)
    id_prediccion = Column(Integer, ForeignKey('prediccion_abastecimiento.id_prediccion'), nullable=True)
    id_sitio = Column(Integer, ForeignKey('sitio.id_sitio'))
    tipo_alerta = Column(SQLAlchemyEnum(TipoAlertaEnum), nullable=False)
    estado_alerta = Column(SQLAlchemyEnum(EstadoAlertaEnum), default=EstadoAlertaEnum.ABIERTA)
    mensaje = Column(String(255))
    creado_en = Column(TIMESTAMP, server_default=func.now())
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    prediccion = relationship("PrediccionAbastecimiento", back_populates="alertas")
    sitio = relationship("Sitio", back_populates="alertas")
    notificaciones_log = relationship("NotificacionLog", back_populates="alerta")

class NotificacionConfiguracion(Base):
    __tablename__ = 'notificacion_configuracion'
    id_configuracion = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'))
    tipo_alerta = Column(SQLAlchemyEnum(TipoAlertaNotificacionEnum))
    canal_envio = Column(SQLAlchemyEnum(CanalEnvioEnum))
    activado = Column(Boolean, default=True)
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relación
    usuario = relationship("Usuario", back_populates="notificaciones_config")

class NotificacionLog(Base):
    __tablename__ = 'notificacion_log'
    id_notificacion = Column(Integer, primary_key=True)
    id_alerta = Column(Integer, ForeignKey('alerta.id_alerta'), nullable=True)
    id_abastecimiento = Column(Integer, ForeignKey('abastecimiento.id_abastecimiento'), nullable=True)
    id_usuario_destino = Column(Integer, ForeignKey('usuario.id_usuario'))
    canal_envio = Column(SQLAlchemyEnum(CanalEnvioEnum))
    direccion_destino = Column(String(160))
    estado_envio = Column(SQLAlchemyEnum(EstadoEnvioEnum))
    respuesta_proveedor = Column(String(255), nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    # Relaciones
    alerta = relationship("Alerta", back_populates="notificaciones_log")
    abastecimiento = relationship("Abastecimiento", back_populates="notificaciones_log")
    usuario_destino = relationship("Usuario", back_populates="notificaciones_recibidas")