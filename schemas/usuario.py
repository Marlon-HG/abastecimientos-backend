from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

# --- Schema para el Rol ---
class Rol(BaseModel):
    id_rol: int
    nombre: str
    class Config:
        from_attributes = True

# --- Schema Base ---
class UsuarioBase(BaseModel):
    nombre_completo: str
    correo: EmailStr

# --- Schema para la Creación ---
class UsuarioCreate(UsuarioBase):
    contrasena: str
    id_rol: int

# --- Schema para la Lectura (respuesta de la API) ---
class Usuario(UsuarioBase):
    id_usuario: int
    activo: bool
    creado_en: datetime
    actualizado_en: datetime
    roles: List[Rol] = []

    class Config:
        from_attributes = True

# --- Schemas para Recuperación de Contraseña (Público) ---
class RequestPasswordReset(BaseModel):
    correo: EmailStr

class ResetPassword(BaseModel):
    token: str
    nueva_contrasena: str

# --- Schema para cambio verificando la contraseña actual ---
class UsuarioChangePasswordWithVerification(BaseModel):
    contrasena_actual: str
    nueva_contrasena: str

# --- NUEVO SCHEMA: Para cambio directo de contraseña (usuario autenticado) ---
class UsuarioUpdatePassword(BaseModel):
    nueva_contrasena: str

# --- Otros Schemas de Utilidad ---
class UsuarioAssignRoles(BaseModel):
    id_usuario: int
    roles_ids: List[int]

class UsuarioSimple(BaseModel):
    correo: str
    activo: bool
    class Config:
        from_attributes = True

class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    correo: Optional[EmailStr] = None
    activo: Optional[bool] = None
    id_rol: Optional[int] = None