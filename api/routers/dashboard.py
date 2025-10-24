# api/routers/dashboard.py
from fastapi import APIRouter, Depends, HTTPException # <-- AÑADIR HTTPException
from sqlalchemy.orm import Session
from api import deps
from db import models
from services import dashboard_service
from schemas import dashboard as dashboard_schema # Asegúrate de tener este esquema

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/", response_model=dashboard_schema.DashboardData)
def get_dashboard_data(
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_user)
):
    """
    Endpoint para obtener las estadísticas del dashboard.
    """
    stats = dashboard_service.get_dashboard_stats(db, current_user=current_user)

    if isinstance(stats, dict) and "error" in stats:
         print(f"Error obteniendo estadísticas del dashboard: {stats['error']}")
         # Ahora sí podemos lanzar la excepción si queremos
         raise HTTPException(status_code=404, detail=stats["error"])
         # O devolver datos por defecto:
         # return dashboard_schema.DashboardData(
         #      total_abastecimientos_mes=0, total_galones_mes=0.0, ... etc.
         # )

    # Crear el objeto Pydantic (esto fallará si faltan campos en stats)
    try:
        return dashboard_schema.DashboardData(**stats)
    except Exception as e:
        print(f"Error al convertir estadísticas a Pydantic: {e}")
        # La HTTPException ya está importada
        raise HTTPException(status_code=500, detail="Error interno al procesar datos del dashboard.")