# C:\Users\marlo\Desktop\abastecimientos_backend\schemas\supervisor.py
from pydantic import BaseModel
from typing import Optional

# --- Esquema simple para la respuesta ---
class ContratistaSimple(BaseModel):
    nombre_contrata: str
    class Config:
        from_attributes = True

# --- Esquema Base (atributos comunes) ---
class SupervisorBase(BaseModel):
    nombre_completo: str
    correo: str
    telefono: str  # <-- AÑADIDO (es requerido por la DB)
    id_contratista: Optional[int] = None

# --- Esquema para Creación (usado en POST) ---
class SupervisorCreate(SupervisorBase):
    pass

# --- Esquema para Actualización (usado en PUT) ---
class SupervisorUpdate(SupervisorBase):
    # Hacemos todos los campos opcionales para el PUT
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None # <-- AÑADIDO
    id_contratista: Optional[int] = None

# --- Esquema de Respuesta (el que ya tenías) ---
class Supervisor(SupervisorBase):
    id_supervisor: int
    contratista: Optional[ContratistaSimple] = None

    class Config:
        from_attributes = True