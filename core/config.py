# Lógica para cargar variables de entorno desde .env
#core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Variables de seguridad y base de datos
    SECRET_KEY: str
    ALGORITHM: str  # <-- AÑADIDA
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # <-- AÑADIDA
    DATABASE_URL: str

    # --- NUEVAS VARIABLES PARA EL CORREO ---
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()