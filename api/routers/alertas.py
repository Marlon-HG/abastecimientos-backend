from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api import deps
from db import models  # Importa los modelos base
from schemas import alerta as alerta_schema # Importa schemas/alerta.py
from crud import alerta as alerta_crud # Importa crud/alerta.py
from services import alert_service

# Importar los Enums específicos que necesitas usar en este archivo
from db.models import EstadoAlertaEnum, TipoAlertaEnum

router = APIRouter(
    prefix="/alertas",
    tags=["Alertas"]
)


@router.get(
    "/",
    response_model=List[alerta_schema.AlertaDetails],
    summary="Leer Alertas Abiertas"
)
def read_open_alerts(
        db: Session = Depends(deps.get_db),
        # --- Dependencia de usuario REQUERIDA para proteger el endpoint ---
        current_user: models.Usuario = Depends(deps.get_current_active_user)
):
    """
    Obtiene una lista de todas las alertas que están actualmente en estado 'ABIERTA'.
    """
    alerts = alerta_crud.get_open_alerts(db)
    return alerts


@router.post(
    "/generar",
    summary="Generar Predicciones y Alertas"
)
async def generar_alertas(
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_admin_user)  # Solo Admins
):
    """
    Dispara el proceso de cálculo de predicciones para todos los sitios
    y la generación de nuevas alertas si es necesario.
    """
    resultado = await alert_service.generar_alertas_de_predicciones(db)
    return resultado


@router.put(
    "/{alerta_id}/cerrar",
    response_model=alerta_schema.Alerta,
    summary="Cerrar una Alerta"
)
def close_alert(
        alerta_id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_active_user)
):
    """
    Marca una alerta específica como 'CERRADA'.
    """
    print(f"Usuario {current_user.correo} intentando cerrar alerta ID: {alerta_id}")  # DEBUG

    db_alerta = alerta_crud.get_alert_by_id(db, alerta_id=alerta_id)
    if not db_alerta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")

    # Usar el Enum correcto 'EstadoAlertaEnum'
    if db_alerta.estado_alerta == EstadoAlertaEnum.CERRADA:
        print("-> La alerta ya estaba cerrada.")  # DEBUG
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La alerta ya se encuentra cerrada."
        )

    closed_alert = alerta_crud.close_alert(db, db_alerta=db_alerta)

    return closed_alert