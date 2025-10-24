#db/base.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Crea la URL de conexión usando la configuración cargada desde .env
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Crea el motor (engine) de SQLAlchemy
# El argumento 'pool_pre_ping=True' verifica las conexiones antes de usarlas,
# lo que previene errores por conexiones cerradas por el servidor de BD.
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# Crea una fábrica de sesiones (SessionLocal) que se usará para crear
# nuevas sesiones de base de datos para cada solicitud.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crea una clase Base que servirá como la clase base para todos tus
# modelos de SQLAlchemy. Tus modelos heredarán de esta clase.
Base = declarative_base()