from sqlalchemy.orm import Session, joinedload
from db import models
from schemas import tecnico as tecnico_schema, usuario as usuario_schema
from crud import usuario as usuario_crud
from fastapi import HTTPException, status


def get_tecnicos(db: Session, skip: int = 0, limit: int = 100):
    # --- CORRECCIÓN AQUÍ ---
    # Se añaden ambos joinedload para cargar las relaciones de grupo y contratista
    return db.query(models.Tecnico).options(
        joinedload(models.Tecnico.grupo_tecnico),
        joinedload(models.Tecnico.contratista) # <-- Esta línea carga los datos del contratista
    ).offset(skip).limit(limit).all()


def create_tecnico(db: Session, tecnico: tecnico_schema.TecnicoCreate):
    rol_tecnico = db.query(models.Rol).filter(models.Rol.nombre == models.RolEnum.TECNICO).first()
    if not rol_tecnico:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El rol 'tecnico' no ha sido encontrado en la base de datos."
        )

    db_user_check = usuario_crud.get_user_by_email(db, email=tecnico.correo_tecnico)
    if db_user_check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado por otro usuario."
        )

    usuario_data = usuario_schema.UsuarioCreate(
        nombre_completo=tecnico.nombre_completo_usuario,
        correo=tecnico.correo_tecnico,
        contrasena=tecnico.contrasena_usuario,
        id_rol=rol_tecnico.id_rol
    )

    nuevo_usuario = usuario_crud.create_user(db, user=usuario_data)

    db_tecnico = models.Tecnico(
        id_usuario=nuevo_usuario.id_usuario,
        nombre_tecnico=tecnico.nombre_tecnico,
        dpi_tecnico=tecnico.dpi_tecnico,
        correo_tecnico=tecnico.correo_tecnico,
        cel_tecnico_contrata=tecnico.cel_tecnico_contrata,
        cel_tecnico_personal=tecnico.cel_tecnico_personal,
        fec_nac_tecnico=tecnico.fec_nac_tecnico,
        id_grupo=tecnico.id_grupo,
        id_contratista=tecnico.id_contratista,
        status=tecnico.status
    )

    db.add(db_tecnico)
    db.commit()
    db.refresh(db_tecnico)
    return db_tecnico


def update_tecnico(db: Session, tecnico_id: int, tecnico_update: tecnico_schema.TecnicoUpdate):
    db_tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == tecnico_id).first()
    if not db_tecnico:
        return None

    update_data = tecnico_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tecnico, key, value)

    db.add(db_tecnico)
    db.commit()
    db.refresh(db_tecnico)
    return db_tecnico


def delete_tecnico(db: Session, tecnico_id: int):
    db_tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == tecnico_id).first()
    if not db_tecnico:
        return None

    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == db_tecnico.id_usuario).first()
    if db_usuario:
        db.delete(db_usuario)
        db.commit()
        return db_tecnico
    return None