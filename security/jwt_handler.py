#security/jwt_handler.py

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from core.config import settings
from schemas import token as token_schema

# Clave secreta para firmar el token (leída desde .env)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # El token será válido por 60 minutos


def create_access_token(data: dict):
    """Crea un nuevo token de acceso JWT."""
    to_encode = data.copy()

    # Establece la fecha de expiración del token
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Codifica el token con el payload, la clave secreta y el algoritmo
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """Verifica y decodifica un token de acceso JWT."""
    try:
        # Intenta decodificar el token usando la clave secreta y el algoritmo
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise credentials_exception
        # Devuelve los datos del token si la decodificación es exitosa
        return token_schema.TokenData(correo=correo)
    except JWTError:
        # Si el token no es válido (firma incorrecta, expirado, etc.), lanza una excepción
        raise credentials_exception