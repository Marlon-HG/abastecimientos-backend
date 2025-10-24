# crud/prediccion.py
from sqlalchemy.orm import Session
from db import models
# No necesitas importar el schema aquí si recibes un dict
# from schemas import prediccion as prediccion_schema
from datetime import datetime

def create_or_update_prediccion(db: Session, prediccion_data: dict):
    """
    Busca una predicción existente para el sitio. Si existe, la actualiza.
    Si no existe, crea un nuevo registro.
    'prediccion_data' debe ser un diccionario con las claves correctas del modelo.
    """
    # 1. Buscar predicción existente
    db_prediccion = db.query(models.PrediccionAbastecimiento).filter(
        models.PrediccionAbastecimiento.id_sitio == prediccion_data["id_sitio"]
    ).first()

    if db_prediccion:
        # --- 2. Si existe, ACTUALIZAR ---
        # --- CORRECCIÓN: No actualizar fecha_prediccion ---
        # db_prediccion.fecha_prediccion = datetime.now() # Eliminado
        # --- FIN CORRECCIÓN ---
        db_prediccion.fecha_proximo_abastecimiento = prediccion_data["fecha_proximo_abastecimiento"]
        # Usar .get() por si no viene en el dict, aunque debería
        db_prediccion.horometro_estimado_fin = prediccion_data.get("horometro_estimado_fin")
        db_prediccion.id_ultimo_abastecimiento_usado = prediccion_data["id_ultimo_abastecimiento_usado"]
        # Nota: creado_en no se actualiza aquí, se mantiene el original.
        # Si quisieras actualizar una marca de tiempo, necesitarías un campo 'actualizado_en' en el modelo.
    else:
        # --- 3. Si no existe, CREAR ---
        # --- CORRECCIÓN: No pasar fecha_prediccion ---
        db_prediccion = models.PrediccionAbastecimiento(
            id_sitio=prediccion_data["id_sitio"],
            # fecha_prediccion=datetime.now(), # Eliminado
            fecha_proximo_abastecimiento=prediccion_data["fecha_proximo_abastecimiento"],
            horometro_estimado_fin=prediccion_data.get("horometro_estimado_fin"),
            id_ultimo_abastecimiento_usado=prediccion_data["id_ultimo_abastecimiento_usado"]
            # creado_en se llenará automáticamente por la BD
        )
        # --- FIN CORRECCIÓN ---

    # 4. Guardar cambios
    try:
        db.add(db_prediccion)
        db.commit()
        db.refresh(db_prediccion)
        return db_prediccion
    except Exception as e:
        db.rollback() # Deshacer cambios si hay error
        print(f"Error en CRUD al guardar predicción: {e}")
        # Podrías relanzar la excepción o devolver None/manejar el error
        raise e # Relanzar para que el servicio lo maneje