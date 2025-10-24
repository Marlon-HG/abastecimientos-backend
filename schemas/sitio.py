from pydantic import BaseModel
from typing import Optional
# Asume que estos schemas existen en sus respectivos archivos .py
from . import supervisor as supervisor_schema
from . import tecnico as tecnico_schema
from . import tipo_sitio as tipo_sitio_schema
from . import contratista as contratista_schema # Asume que tienes este schema

# --- Schema Base ---
# Campos comunes para crear y leer
class SitioBase(BaseModel):
    id: str # El ID de texto (ej: TTN015)
    nombre: str
    departamento: str
    municipio: str
    dir_detallada: Optional[str] = None
    latitud: Optional[str] = None
    longitud: Optional[str] = None

# --- Schema para Crear ---
# Campos necesarios al crear un sitio nuevo (IDs de relaciones)
class SitioCreate(SitioBase):
    id_tecnico: int
    id_supervisor: int
    id_tipo_sitio: int
    id_contratista: int

# --- Schema para Actualizar ---
# Todos los campos son opcionales para permitir actualizaciones parciales
class SitioUpdate(BaseModel):
    id: Optional[str] = None # Permitir cambiar el ID de texto? Considerar si es buena idea
    nombre: Optional[str] = None
    departamento: Optional[str] = None
    municipio: Optional[str] = None
    dir_detallada: Optional[str] = None
    latitud: Optional[str] = None
    longitud: Optional[str] = None
    id_tecnico: Optional[int] = None
    id_supervisor: Optional[int] = None
    id_tipo_sitio: Optional[int] = None
    id_contratista: Optional[int] = None

# --- Schema para Respuestas (Completo) ---
# Este es el schema principal que se usa al devolver datos de un sitio
class Sitio(SitioBase):
    id_sitio: int # El ID numérico de la base de datos
    id_contratista: int
    id_tecnico: int
    id_supervisor: int
    id_tipo_sitio: int

    # Incluir objetos anidados para mostrar información más completa en la respuesta
    # Asegúrate que los schemas referenciados (TipoSitio, Supervisor, Tecnico) tengan 'from_attributes = True'
    tipo_sitio: Optional[tipo_sitio_schema.TipoSitio] = None
    supervisor: Optional[supervisor_schema.Supervisor] = None
    tecnico: Optional[tecnico_schema.Tecnico] = None
    # Podrías añadir contratista aquí si tienes el schema y quieres mostrar más que el ID
    # contratista: Optional[contratista_schema.Contratista] = None

    class Config:
        from_attributes = True # Permite crear este schema desde el objeto SQLAlchemy

# --- Schema para Respuestas (Simple) ---
# Un schema más ligero, útil para listas o anidamiento (como en AlertaDetails)
class SitioSimple(BaseModel):
    id_sitio: int
    id: str
    nombre: str

    class Config:
        from_attributes = True