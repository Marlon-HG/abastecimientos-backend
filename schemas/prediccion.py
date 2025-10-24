# C:\Users\marlo\Desktop\abastecimientos_backend\schemas\prediccion.py
from pydantic import BaseModel
from datetime import datetime

class PrediccionBase(BaseModel):
    # Campos base para crear/actualizar (Correctos)
    fecha_proximo_abastecimiento: datetime
    id_ultimo_abastecimiento_usado: int
    horometro_estimado_fin: float

class PrediccionCreate(PrediccionBase):
    # Campo adicional necesario al crear (Correcto)
    id_sitio: int

class Prediccion(PrediccionBase): # Schema para leer desde la BD
    id_prediccion: int
    id_sitio: int
    # --- CORRECCIÓN ---
    # Cambiar fecha_prediccion por creado_en para coincidir con el modelo DB
    creado_en: datetime
    # fecha_prediccion: datetime # <- Eliminar o comentar esta línea
    # --- FIN CORRECCIÓN ---

    class Config:
        from_attributes = True # Permite crear el schema desde el objeto SQLAlchemy