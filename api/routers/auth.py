from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from crud import usuario as usuario_crud
from schemas import token as token_schema
from schemas import usuario as usuario_schema
from security.password_handler import PasswordHandler
from security.jwt_handler import create_access_token
from api import deps
from core.email_service import (
    send_password_reset_email,
    send_password_changed_notification_email
)

router = APIRouter(tags=["Autenticación"])


@router.post("/login", response_model=token_schema.Token)
def login_for_access_token(
        db: Session = Depends(deps.get_db),
        form_data: OAuth2PasswordRequestForm = Depends()
):
    user = usuario_crud.get_user_by_email(db, email=form_data.username)
    if not user or not PasswordHandler.verify_password(form_data.password, user.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene roles asignados y no puede iniciar sesión."
        )

    access_token = create_access_token(
        data={"sub": str(user.id_usuario), "rol": user.roles[0].nombre}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def request_password_reset(
        request_data: usuario_schema.RequestPasswordReset,
        db: Session = Depends(deps.get_db)
):
    user = usuario_crud.get_user_by_email(db, email=request_data.correo)
    if user:
        token = usuario_crud.set_password_reset_token(db, user=user)

        await send_password_reset_email(
            db=db,
            user_id=user.id_usuario,
            email_to=user.correo,
            nombre_usuario=user.nombre_completo,
            token=token
        )
    return {"msg": "Si existe una cuenta con este correo, se ha enviado un enlace para restablecer la contraseña."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
        reset_data: usuario_schema.ResetPassword,
        db: Session = Depends(deps.get_db)
):
    user = usuario_crud.get_user_by_reset_token(db, token=reset_data.token)

    if not user or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token es inválido o ha expirado."
        )

    user_id = user.id_usuario  # Guardamos el ID antes de hacer commit
    user_email = user.correo
    user_name = user.nombre_completo

    hashed_password = PasswordHandler.get_password_hash(reset_data.nueva_contrasena)
    user.contrasena = hashed_password
    user.reset_token = None
    user.reset_token_expires = None

    db.add(user)
    db.commit()

    # --- CORRECCIÓN AQUÍ ---
    # Añadimos los argumentos 'db' y 'user_id' que faltaban en la llamada
    await send_password_changed_notification_email(
        db=db,
        user_id=user_id,
        email_to=user_email,
        nombre_usuario=user_name
    )

    return {"msg": "Contraseña restablecida con éxito."}