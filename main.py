# C:\Users\marlo\Desktop\abastecimientos_backend\main.py
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

# --- CORRECCIÓN ---
# Añade la URL de tu frontend en Vercel a la lista de orígenes
origins = [
    "https://abastecimientos-frontend.vercel.app", # <-- URL de producción (Vercel)
    "http://localhost:5173",                      # URL de desarrollo local (Vite)
    "http://localhost:3000",                      # URL de desarrollo local (CRA)
]
# --- FIN CORRECCIÓN ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # <-- Usa la lista actualizada
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