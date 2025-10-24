from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# --- 1. IMPORTA EL NUEVO ROUTER AQUÍ ---
from api.routers import (
    usuarios,
    auth,
    roles,
    abastecimientos,
    predicciones,
    sitios,
    tecnicos,
    supervisores,
    alertas,
    configuracion_notificaciones,
    dashboard,
    grupo_tecnico,
    contratistas,
    tipos_sitio
)

app = FastAPI(title="Abastecimientos API")

# Configuración de CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclusión de los routers en la aplicación principal
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(roles.router)
app.include_router(abastecimientos.router)
app.include_router(sitios.router)
app.include_router(tecnicos.router)
app.include_router(supervisores.router)
app.include_router(alertas.router)
app.include_router(predicciones.router)
app.include_router(configuracion_notificaciones.router)
app.include_router(dashboard.router)
app.include_router(grupo_tecnico.router)
app.include_router(contratistas.router)
app.include_router(tipos_sitio.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Abastecimientos Tigo"}

# Forzar build