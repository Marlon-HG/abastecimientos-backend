import os

# Nombre del directorio raíz del proyecto (lo dejamos vacío si el script se ejecuta en la raíz)
PROJECT_ROOT = ""

# Lista de directorios a crear. Las tuplas anidadas representan subdirectorios.
DIRECTORIES = [
    "api",
    ("api", "routers"),
    "core",
    "db",
    "schemas",
    "services",
    "security",
]

# Lista de archivos a crear. Las tuplas representan la ruta (directorio, archivo).
# Usamos 'pass' como contenido inicial para crear archivos .py válidos.
FILES = {
    # Nivel Raíz
    ".env": "SECRET_KEY=tu_super_secreto_aqui\nDATABASE_URL=mysql+pymysql://user:password@host/db_name",
    ".gitignore": "*.pyc\n__pycache__/\n.venv\n.env\n",
    "requirements.txt": "fastapi\nuvicorn[standard]\nSQLAlchemy\nPMySQL\npython-jose[cryptography]\npasslib[bcrypt]\npydantic[email]\npython-dotenv\n",
    "main.py": "from fastapi import FastAPI\n\napp = FastAPI(title=\"Abastecimientos API\")\n\n@app.get(\"/\")\ndef read_root():\n    return {\"message\": \"Bienvenido a la API de Abastecimientos Tigo\"}\n",

    # Directorio API
    ("api", "__init__.py"): "",
    ("api", "deps.py"): "# Dependencias para inyectar en las rutas (ej. get_current_user)\npass\n",
    ("api", "routers", "__init__.py"): "",
    ("api", "routers",
     "auth.py"): "# Endpoints para autenticación (/login, /token)\nfrom fastapi import APIRouter\n\nrouter = APIRouter()\n",
    ("api", "routers",
     "abastecimientos.py"): "# Endpoints para gestionar abastecimientos (CRUD)\nfrom fastapi import APIRouter\n\nrouter = APIRouter()\n",
    ("api", "routers",
     "usuarios.py"): "# Endpoints para gestionar usuarios (CRUD)\nfrom fastapi import APIRouter\n\nrouter = APIRouter()\n",

    # Directorio Core
    ("core", "__init__.py"): "",
    ("core",
     "config.py"): "# Lógica para cargar variables de entorno desde .env\nfrom pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    SECRET_KEY: str\n    DATABASE_URL: str\n\n    class Config:\n        env_file = \".env\"\n\nsettings = Settings()\n",

    # Directorio DB
    ("db", "__init__.py"): "",
    ("db", "base.py"): "# Configuración del motor y la sesión de SQLAlchemy\npass\n",
    ("db", "models.py"): "# Definición de los modelos de SQLAlchemy (tablas)\npass\n",

    # Directorio Schemas
    ("schemas", "__init__.py"): "",
    ("schemas", "abastecimiento.py"): "# Esquemas Pydantic para Abastecimiento\npass\n",
    ("schemas", "token.py"): "# Esquemas Pydantic para Tokens JWT\npass\n",
    ("schemas", "usuario.py"): "# Esquemas Pydantic para Usuario\npass\n",

    # Directorio Services
    ("services", "__init__.py"): "",
    ("services", "prediction_service.py"): "# Lógica para el cálculo de la predicción\npass\n",

    # Directorio Security
    ("security", "__init__.py"): "",
    ("security", "jwt_handler.py"): "# Funciones para crear y validar tokens JWT\npass\n",
}


def create_project_structure():
    """Crea la estructura de directorios y archivos para el proyecto."""
    print("🚀 Iniciando la creación de la estructura del proyecto...")

    # Crear directorios
    for path_parts in DIRECTORIES:
        if isinstance(path_parts, tuple):
            full_path = os.path.join(PROJECT_ROOT, *path_parts)
        else:
            full_path = os.path.join(PROJECT_ROOT, path_parts)

        os.makedirs(full_path, exist_ok=True)
        print(f"   -> Directorio creado: {full_path}")

    # Crear archivos
    for path_parts, content in FILES.items():
        if isinstance(path_parts, tuple):
            full_path = os.path.join(PROJECT_ROOT, *path_parts)
        else:
            full_path = os.path.join(PROJECT_ROOT, path_parts)

        # --- INICIO DE LA CORRECCIÓN ---
        # Asegurarse de que el directorio del archivo exista, solo si no es la raíz.
        dir_name = os.path.dirname(full_path)
        if dir_name:  # Solo ejecutar si dir_name no es una cadena vacía
            os.makedirs(dir_name, exist_ok=True)
        # --- FIN DE LA CORRECCIÓN ---

        if not os.path.exists(full_path):
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            print(f"   -> Archivo creado:    {full_path}")
        else:
            print(f"   -> Archivo ya existe: {full_path}")

    print("\n✅ ¡Estructura del proyecto creada con éxito!")
    print("Ahora puedes eliminar este script.")


if __name__ == "__main__":
    create_project_structure()