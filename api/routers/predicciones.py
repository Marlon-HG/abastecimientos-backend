from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api import deps
from db import models
from services import prediction_service
from schemas import prediccion as prediccion_schema

router = APIRouter(
    prefix="/predicciones",
    tags=["Predicciones"]
)

@router.post("/{sitio_id}", response_model=prediccion_schema.Prediccion)
def get_prediction_for_sitio(
        sitio_id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.Usuario = Depends(deps.get_current_user)
):
    """
    Calcula y guarda la predicción de próximo abastecimiento para un sitio.
    """
    # El servicio ahora devuelve el objeto de la base de datos o un dict de error
    resultado = prediction_service.calculate_prediction(db, sitio_id)

    # Si es un dict, es un error
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(
            status_code=400,
            detail=resultado["error"]
        )

    # Si no es un error, es el objeto de la DB, que coincide con el response_model
    return resultado