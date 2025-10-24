from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from schemas import usuario as usuario_schema
from crud import usuario as usuario_crud
from api import deps
from db import models
from core.email_service import send_password_changed_notification_email, send_welcome_email
from security.password_handler import PasswordHandler

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


# --- NUEVO ENDPOINT PARA CAMBIO DIRECTO DE CONTRASEÑA ---
@router.put("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_current_user_password(
        password_data: usuario_schema.UsuarioUpdatePassword,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_user)
):
    """
    Permite al usuario autenticado cambiar su propia contraseña directamente,
    sin proporcionar la contraseña actual.
    """
    if len(password_data.nueva_contrasena) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres."
        )

    hashed_password = PasswordHandler.get_password_hash(password_data.nueva_contrasena)
    current_user.contrasena = hashed_password
    db.commit()

    # Notificar al usuario sobre el cambio
    await send_password_changed_notification_email(
        email_to=current_user.correo,
        nombre_usuario=current_user.nombre_completo
    )
    return


# --- ENDPOINTS EXISTENTES (Se mantienen sin cambios) ---

@router.get("/", response_model=List[usuario_schema.Usuario])
def read_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    users = usuario_crud.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/signup", response_model=usuario_schema.Usuario, status_code=status.HTTP_201_CREATED)
async def signup_new_user(user_data: usuario_schema.UsuarioCreate, db: Session = Depends(deps.get_db)):
    db_user = usuario_crud.get_user_by_email(db, email=user_data.correo)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )
    new_user = usuario_crud.create_user(db=db, user=user_data)
    await send_welcome_email(
        db=db,
        user_id=new_user.id_usuario,
        email_to=new_user.correo,
        nombre_usuario=new_user.nombre_completo,
        contrasena=user_data.contrasena
    )
    return new_user


@router.post("/admin-create", response_model=usuario_schema.Usuario, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
        user_data: usuario_schema.UsuarioCreate,
        db: Session = Depends(deps.get_db),
        admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    db_user = usuario_crud.get_user_by_email(db, email=user_data.correo)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )
    new_user = usuario_crud.create_user(db=db, user=user_data)
    await send_welcome_email(
        db=db,
        user_id=new_user.id_usuario,
        email_to=new_user.correo,
        nombre_usuario=new_user.nombre_completo,
        contrasena=user_data.contrasena
    )
    return new_user


@router.get("/me", response_model=usuario_schema.Usuario)
def read_users_me(
        current_user: models.Usuario = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db)
):
    # Ya que deps.get_current_user devuelve el objeto de usuario completo,
    # no es necesario volver a consultarlo.
    return current_user


@router.post("/assign-roles", response_model=usuario_schema.Usuario)
def assign_roles(
        assignment_data: usuario_schema.UsuarioAssignRoles,
        db: Session = Depends(deps.get_db),
        admin_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    updated_user = usuario_crud.assign_roles_to_user(
        db,
        user_id=assignment_data.id_usuario,
        roles_ids=assignment_data.roles_ids
    )
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {assignment_data.id_usuario} no encontrado."
        )
    return updated_user


# El endpoint anterior se renombra para mayor claridad
@router.post("/me/verify-and-change-password", status_code=status.HTTP_200_OK)
async def verify_and_change_password(
        password_data: usuario_schema.UsuarioChangePasswordWithVerification,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_user)
):
    if not PasswordHandler.verify_password(password_data.contrasena_actual, current_user.contrasena):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta."
        )
    hashed_password = PasswordHandler.get_password_hash(password_data.nueva_contrasena)
    current_user.contrasena = hashed_password
    db.add(current_user)
    db.commit()
    await send_password_changed_notification_email(
        email_to=current_user.correo,
        nombre_usuario=current_user.nombre_completo
    )
    return {"msg": "Contraseña cambiada con éxito."}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_admin(
        user_id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    if current_user.id_usuario == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes eliminar tu propia cuenta de administrador."
        )
    deleted_user = usuario_crud.delete_user(db, user_id=user_id)
    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {user_id} no encontrado."
        )
    return


@router.put("/{user_id}", response_model=usuario_schema.Usuario)
def update_user_by_admin(
        user_id: int,
        user_data: usuario_schema.UsuarioUpdate,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)
):
    updated_user = usuario_crud.update_user(db, user_id=user_id, user_update=user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {user_id} no encontrado."
        )
    return updated_user