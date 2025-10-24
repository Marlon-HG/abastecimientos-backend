# schemas/dashboard.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional # <-- Necesitas Optional
from datetime import datetime

# Esquema para un punto de datos del gráfico (sin cambios)
class ChartDataPoint(BaseModel):
    label: str
    value: float

# --- Esquema para un sitio crítico (MODIFICADO) ---
class SitioCriticoInfo(BaseModel):
    id_sitio: int
    nombre_sitio: str
    fecha_proximo_abastecimiento: str # O datetime
    # --- AÑADIDO ---
    dias_restantes: Optional[float] = None # Añade este campo
    # --- FIN AÑADIDO ---

    class Config:
        from_attributes = True

# Esquema para un abastecimiento reciente (sin cambios)
class AbastecimientoRecienteInfo(BaseModel):
    id_abastecimiento: int
    nombre_sitio: str
    fecha: str # O datetime
    galones_abastecidos: float

# Esquema principal del Dashboard (sin cambios)
class DashboardData(BaseModel):
    total_sitios: int
    total_abastecimientos_mes: int
    total_galones_mes: float
    sitios_proximo_abastecimiento: int
    alertas_abiertas: int
    total_galones_ultimos_30_dias: float
    abastecimientos_ultimos_30_dias: int
    # El tipo aquí ya debería ser List[SitioCriticoInfo]
    sitios_criticos: List[SitioCriticoInfo]
    galones_por_dia_chart: List[ChartDataPoint]
    ultimos_abastecimientos: List[AbastecimientoRecienteInfo]
    sitios_menor_nivel: List[Any]