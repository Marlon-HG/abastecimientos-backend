from pydantic import BaseModel
from typing import Optional

# --- CLASE AÑADIDA ---
# Este es el schema para los datos que están DENTRO del token JWT.
# 'sub' es el nombre estándar para el "subject" (sujeto), que en nuestro caso es el ID del usuario.
class TokenPayload(BaseModel):
    sub: int

# Este es el schema para la RESPUESTA que se envía al frontend después de un login exitoso.
class Token(BaseModel):
    access_token: str
    token_type: str

# Esta clase es de una versión anterior de tu código. La mantenemos por si la usas en otro lugar,
# pero la nueva lógica de 'deps.py' ya no la necesita.
class TokenData(BaseModel):
    username: Optional[str] = None