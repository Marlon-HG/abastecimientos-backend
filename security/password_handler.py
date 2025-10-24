#security/password_handler.py

from passlib.context import CryptContext

# Creamos un contexto para el hash, especificando el algoritmo a usar (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordHandler:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña en texto plano coincide con su hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Genera el hash de una contraseña en texto plano."""
        return pwd_context.hash(password)