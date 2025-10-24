from sqlalchemy.orm import Session, joinedload
from db import models
from schemas import usuario as usuario_schema
from security.password_handler import PasswordHandler
import secrets
from datetime import datetime, timedelta
from core.config import settings
from typing import List  # <-- IMPORTACIÓN AÑADIDA


def get_user_by_email(db: Session, email: str):
    """Busca y devuelve un usuario por su correo electrónico."""
    return db.query(models.Usuario).filter(models.Usuario.correo == email).first()


def get_user(db: Session, user_id: int):
    """
    Busca y devuelve un usuario por su ID, forzando la carga de su perfil
    de técnico y sus roles en la misma consulta.
    """
    return db.query(models.Usuario).options(
        joinedload(models.Usuario.tecnico),
        joinedload(models.Usuario.roles)
    ).filter(models.Usuario.id_usuario == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Devuelve una lista de todos los usuarios."""
    return db.query(models.Usuario).offset(skip).limit(limit).all()


def set_password_reset_token(db: Session, user: models.Usuario) -> str:
    """Genera, guarda y devuelve un token de reseteo de contraseña."""
    token = secrets.token_urlsafe(32)
    expire_delta = timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + expire_delta

    db.add(user)
    db.commit()

    return token


def get_user_by_reset_token(db: Session, token: str) -> models.Usuario | None:
    """Busca un usuario por su token de reseteo de contraseña."""
    return db.query(models.Usuario).filter(models.Usuario.reset_token == token).first()


def create_user(db: Session, user: usuario_schema.UsuarioCreate):
    """Crea un nuevo usuario en la base de datos."""
    hashed_password = PasswordHandler.get_password_hash(user.contrasena)

    rol = db.query(models.Rol).filter(models.Rol.id_rol == user.id_rol).first()
    if not rol:
        return None

    db_user = models.Usuario(
        nombre_completo=user.nombre_completo,
        correo=user.correo,
        contrasena=hashed_password,
        roles=[rol]
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: usuario_schema.UsuarioUpdate):
    """Actualiza un usuario existente."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)

    if "contrasena" in update_data and update_data["contrasena"]:
        hashed_password = PasswordHandler.get_password_hash(update_data["contrasena"])
        update_data["contrasena"] = hashed_password

    if "id_rol" in update_data:
        rol_id = update_data.pop("id_rol")
        rol = db.query(models.Rol).filter(models.Rol.id_rol == rol_id).first()
        if rol:
            db_user.roles = [rol]

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    """Elimina un usuario de la base de datos."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return db_user


def assign_roles_to_user(db: Session, user_id: int, roles_ids: List[int]):
    """Asigna una lista de roles a un usuario."""
    user = get_user(db, user_id=user_id)
    if not user:
        return None

    roles = db.query(models.Rol).filter(models.Rol.id_rol.in_(roles_ids)).all()
    user.roles = roles

    db.commit()
    db.refresh(user)
    return user