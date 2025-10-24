from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, or_  # Importar asc y or_
from db import models
from schemas import abastecimiento as abastecimiento_schema
from typing import Optional, List


# --- FUNCIÓN PARA EL HISTORIAL (CORREGIDA) ---
def get_historial_abastecimientos(
    db: Session,
    current_user: models.Usuario,
    sitio_id: Optional[int] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = 100 # <-- Cambiado a Optional[int]
) -> List[models.Abastecimiento]: # <-- Especificar tipo de retorno
    """
    Obtiene el historial de abastecimientos filtrado por rol y parámetros.
    Si limit es None, devuelve todos los resultados que coincidan (sin paginación).
    """
    user_with_roles = db.query(models.Usuario).options(
        joinedload(models.Usuario.roles),
        joinedload(models.Usuario.tecnico)
    ).filter(models.Usuario.id_usuario == current_user.id_usuario).first()

    if not user_with_roles:
        return []

    user_roles = {rol.nombre for rol in user_with_roles.roles}
    print(f"-> Historial: Usuario {current_user.correo}, Roles cargados: {user_roles}") # DEBUG

    query = db.query(models.Abastecimiento).options(
        joinedload(models.Abastecimiento.sitio) # Cargar sitio para filtros y posible uso
    )

    # Aplicar filtros de rol y búsqueda (lógica sin cambios)
    if 'ADMIN' in user_roles or 'SUPERVISOR' in user_roles:
        print("-> Acceso como ADMIN/SUPERVISOR.") # DEBUG
        if q:
            query = query.join(models.Sitio, models.Abastecimiento.id_sitio == models.Sitio.id_sitio).filter(
                or_(
                    models.Sitio.id.ilike(f"%{q}%"),
                    models.Sitio.nombre.ilike(f"%{q}%"),
                    models.Abastecimiento.ot.ilike(f"%{q}%")
                )
            )
        if sitio_id:
            query = query.filter(models.Abastecimiento.id_sitio == sitio_id)

    elif 'TECNICO' in user_roles:
        print("-> Acceso como TECNICO.") # DEBUG
        tecnico_profile = user_with_roles.tecnico
        if not tecnico_profile:
            print(f"-> Advertencia: Usuario {current_user.correo} rol TECNICO sin perfil.")
            return []

        # Siempre unimos con Sitio para filtrar por tecnico_id
        query = query.join(models.Sitio, models.Abastecimiento.id_sitio == models.Sitio.id_sitio) \
            .filter(models.Sitio.id_tecnico == tecnico_profile.id_tecnico)

        if sitio_id: # Filtro adicional sobre los sitios del técnico
            query = query.filter(models.Abastecimiento.id_sitio == sitio_id)
        if q: # Filtro adicional sobre los sitios del técnico
            query = query.filter(
                or_(
                    models.Sitio.id.ilike(f"%{q}%"),
                    models.Sitio.nombre.ilike(f"%{q}%"),
                    models.Abastecimiento.ot.ilike(f"%{q}%")
                )
            )
    else:
        print(f"-> Usuario {current_user.correo} sin roles válidos.") # DEBUG
        return []

    # Aplicar ordenamiento
    query = query.order_by(desc(models.Abastecimiento.fecha))

    # --- MODIFICACIÓN: Aplicar paginación solo si limit no es None ---
    if limit is not None:
        query = query.offset(skip).limit(limit)
    # --- FIN MODIFICACIÓN ---

    registros = query.all()
    print(f"-> get_historial (limit={limit}): Devolviendo {len(registros)} registros.") # DEBUG
    return registros

# --- FUNCIONES EXISTENTES (CON CORRECCIÓN EN get_abastecimientos_by_sitio) ---
def create_abastecimiento(db: Session, abastecimiento: abastecimiento_schema.AbastecimientoCreate, tecnico_id: int):
    # El argumento tecnico_id no se usa
    db_abastecimiento = models.Abastecimiento(**abastecimiento.model_dump())
    db.add(db_abastecimiento)
    db.commit()
    db.refresh(db_abastecimiento)
    return db_abastecimiento


def get_abastecimientos(db: Session, skip: int = 0, limit: int = 100):
    # Asume que 'status' es un string 'ACTIVO' o un Enum
    # Vamos a usar el Enum si existe, o string si no.
    # Por seguridad, usaremos string 'ACTIVO' como en tu código original
    return db.query(models.Abastecimiento).filter(
        models.Abastecimiento.status == 'ACTIVO'
    ).order_by(
        desc(models.Abastecimiento.fecha)
    ).offset(skip).limit(limit).all()


def get_abastecimientos_by_sitio(db: Session, sitio_id: int):
    """
    Obtiene abastecimientos ACTIVOS de un sitio, ordenados por fecha ASCENDENTE.
    El servicio de predicción NECESITA este orden (asc) para calcular
    diferencias entre registros.
    """
    # --- CORRECCIÓN CRÍTICA PARA PREDICCIONES ---
    return db.query(models.Abastecimiento).filter(
        models.Abastecimiento.id_sitio == sitio_id,
        models.Abastecimiento.status == 'ACTIVO'  # Filtrar solo activos para predicción
    ).order_by(
        asc(models.Abastecimiento.fecha)  # CAMBIADO A asc()
    ).all()


def get_abastecimiento_by_id(db: Session, abastecimiento_id: int):
    return db.query(models.Abastecimiento).options(
        joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.supervisor),
        joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.tecnico)
    ).filter(
        models.Abastecimiento.id_abastecimiento == abastecimiento_id
    ).first()


def update_abastecimiento(db: Session, db_abastecimiento: models.Abastecimiento,
                          abastecimiento_in: abastecimiento_schema.AbastecimientoUpdate):
    update_data = abastecimiento_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_abastecimiento, field, value)
    db.add(db_abastecimiento)
    db.commit()
    db.refresh(db_abastecimiento)
    return db_abastecimiento


def soft_delete_abastecimiento(db: Session, db_abastecimiento: models.Abastecimiento):
    # Asume que 'status' es un string y 'CANCELADO' es un valor válido
    db_abastecimiento.status = 'CANCELADO'
    db.add(db_abastecimiento)
    db.commit()
    db.refresh(db_abastecimiento)
    return db_abastecimiento