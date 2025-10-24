from sqlalchemy.orm import Session
from db import models

def get_tipos_sitio(db: Session):
    return db.query(models.TipoSitio).all()