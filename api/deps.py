from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import ValidationError

from core.config import settings
from db.base import SessionLocal
from db import models
from crud import usuario as usuario_crud
from schemas import token as token_schema


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
        db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.Usuario:
    """
    Dependencia principal: valida el token, busca al usuario por ID y verifica si está activo.
    No verifica roles, solo autentica al usuario.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # --- CORRECCIÓN: Leemos el payload esperando el schema TokenPayload (que busca 'sub') ---
        token_data = token_schema.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise credentials_exception

    # --- CORRECCIÓN CLAVE: Buscamos al usuario por su ID, no por su email ---
    user = usuario_crud.get_user(db, user_id=token_data.sub)

    if user is None:
        raise credentials_exception
    if not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    return user


def get_current_admin_user(
        current_user: models.Usuario = Depends(get_current_user),
) -> models.Usuario:
    """Dependencia de autorización: verifica que el usuario autenticado sea admin."""
    is_admin = any(rol.nombre == models.RolEnum.ADMIN for rol in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes los permisos de administrador necesarios.",
        )
    return current_user


def get_current_supervisor_or_admin_user(
        current_user: models.Usuario = Depends(get_current_user),
) -> models.Usuario:
    """Dependencia de autorización: verifica que el usuario sea supervisor o admin."""
    is_authorized = any(rol.nombre in [models.RolEnum.ADMIN, models.RolEnum.SUPERVISOR] for rol in current_user.roles)
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes los permisos de supervisor o administrador necesarios.",
        )
    return current_user

def get_current_active_user(
        current_user: models.Usuario = Depends(get_current_user),
) -> models.Usuario:
    """Dependencia de autenticación y verificación de estado activo (Alias para get_current_user)."""
    return current_user