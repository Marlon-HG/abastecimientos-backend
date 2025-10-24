from pydantic import BaseModel

class TipoSitio(BaseModel):
    id_tipo_sitio: int
    nombre_tipo_sitio: str

    class Config:
        from_attributes = True