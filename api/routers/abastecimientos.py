# C:\Users\marlo\Desktop\abastecimientos_backend\api\routers\abastecimientos.py
# --- MODIFICADO: Importar StreamingResponse y BytesIO ---
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse # <-- Importar StreamingResponse
from io import BytesIO # <-- Importar BytesIO
# --- FIN MODIFICADO ---
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from schemas import abastecimiento as abastecimiento_schema
from crud import abastecimiento as abastecimiento_crud
from api import deps
from db import models
from services.report_service import generate_historial_pdf
from core import email_service
from services import report_service
import traceback
from datetime import datetime

router = APIRouter(
    prefix="/abastecimientos",
    tags=["Abastecimientos"]
)

# --- ENDPOINT HISTORIAL (sin cambios) ---
@router.get("/historial", response_model=List[abastecimiento_schema.AbastecimientoHistorial])
# ... (código de read_historial sin cambios) ...
def read_historial(
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_user),
    sitio_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, min_length=2, description="Buscar por ID o nombre de sitio"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    historial = abastecimiento_crud.get_historial_abastecimientos(
        db, current_user=current_user, sitio_id=sitio_id, q=q, skip=skip, limit=limit
    )
    return historial


# --- ENDPOINT PARA DESCARGAR HISTORIAL (CORREGIDO con StreamingResponse) ---
@router.get("/historial/descargar")
async def descargar_historial(
    formato: str = Query(..., description="Formato deseado: 'pdf' o 'excel'"),
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_user),
    sitio_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, min_length=2, description="Buscar por ID o nombre de sitio")
):
    historial_completo = abastecimiento_crud.get_historial_abastecimientos(
        db, current_user=current_user, sitio_id=sitio_id, q=q, limit=None
    )

    if not historial_completo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron registros para descargar con los filtros aplicados.")

    file_content: Optional[bytes] = None
    media_type: Optional[str] = None
    filename: str = f"historial_abastecimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if formato.lower() == "pdf":
        try:
            # report_service.generate_historial_pdf ya devuelve bytes
            file_content = report_service.generate_historial_pdf(historial_completo)
            media_type = "application/pdf"
            filename += ".pdf"
        except Exception as e:
            print(f"Error generando PDF del historial: {e}")
            raise HTTPException(status_code=500, detail="Error al generar el archivo PDF.")

    elif formato.lower() == "excel":
        try:
            # report_service.generate_historial_excel ya devuelve bytes
            file_content = report_service.generate_historial_excel(historial_completo)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename += ".xlsx"
        except Exception as e:
            print(f"Error generando Excel del historial: {e}")
            raise HTTPException(status_code=500, detail="Error al generar el archivo Excel.")

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no válido. Use 'pdf' o 'excel'.")

    if file_content is None or media_type is None:
         raise HTTPException(status_code=500, detail="No se pudo generar el contenido del archivo.")

    # --- CORRECCIÓN: Usar StreamingResponse ---
    # Envolver los bytes en un objeto BytesIO para que sea iterable (como un stream)
    content_stream = BytesIO(file_content)

    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    # Devolver StreamingResponse en lugar de Response
    return StreamingResponse(content=content_stream, media_type=media_type, headers=headers)
    # --- FIN CORRECCIÓN ---


# --- ENDPOINT CREAR ABASTECIMIENTO (sin cambios respecto a la versión anterior) ---
@router.post("/", response_model=abastecimiento_schema.Abastecimiento, status_code=status.HTTP_201_CREATED)
# ... (código de create_new_abastecimiento sin cambios) ...
async def create_new_abastecimiento(
    abastecimiento: abastecimiento_schema.AbastecimientoCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_user)
):
    tecnico = current_user.tecnico
    if not tecnico:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario actual no tiene un perfil de técnico asociado.")

    ultimo_abastecimiento = db.query(models.Abastecimiento).filter(
        models.Abastecimiento.id_sitio == abastecimiento.id_sitio,
        models.Abastecimiento.status == 'ACTIVO'
    ).order_by(models.Abastecimiento.fecha.desc()).first()

    if ultimo_abastecimiento and abastecimiento.horometraje <= ultimo_abastecimiento.horometraje:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El horometraje ({abastecimiento.horometraje}) debe ser mayor que el último registro activo ({ultimo_abastecimiento.horometraje})."
        )

    try:
        new_abastecimiento = abastecimiento_crud.create_abastecimiento(
            db=db, abastecimiento=abastecimiento, tecnico_id=tecnico.id_tecnico
        )
        db.refresh(new_abastecimiento)

        reloaded_abastecimiento = db.query(models.Abastecimiento).options(
            joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.supervisor),
            joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.tecnico).joinedload(models.Tecnico.usuario)
        ).filter(models.Abastecimiento.id_abastecimiento == new_abastecimiento.id_abastecimiento).first()

        if not reloaded_abastecimiento:
             print(f"Error: No se pudo recargar Abastecimiento ID {new_abastecimiento.id_abastecimiento}")
             return new_abastecimiento

    except Exception as e:
        print(f"Error crítico al crear/recargar abastecimiento: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al guardar el registro.")

    try:
        pdf_bytes = generate_historial_pdf(reloaded_abastecimiento) # Llamada directa a la función importada

        fecha_filename = reloaded_abastecimiento.fecha.strftime('%Y%m%d_%H%M') if isinstance(reloaded_abastecimiento.fecha, datetime) else "fecha_invalida"
        sitio_nombre_filename = reloaded_abastecimiento.sitio.nombre.replace(" ", "_").replace("/", "-") if reloaded_abastecimiento.sitio else "SitioID"+str(reloaded_abastecimiento.id_sitio)
        filename = f"Reporte_Abastecimiento_{sitio_nombre_filename}_{fecha_filename}.pdf"

        recipients_data: Dict[str, tuple[Optional[int], str]] = {}
        site_technician = reloaded_abastecimiento.sitio.tecnico if reloaded_abastecimiento.sitio else None
        if (site_technician and site_technician.usuario and site_technician.usuario.correo):
            email_tec_sitio = site_technician.usuario.correo
            if email_tec_sitio not in recipients_data:
                recipients_data[email_tec_sitio] = (site_technician.usuario.id_usuario, site_technician.nombre_tecnico)
        site_supervisor = reloaded_abastecimiento.sitio.supervisor if reloaded_abastecimiento.sitio else None
        if (site_supervisor and site_supervisor.correo):
             email_sup = site_supervisor.correo
             if email_sup not in recipients_data:
                 recipients_data[email_sup] = (None, site_supervisor.nombre_completo)

        if recipients_data:
            print(f"-> Enviando PDF para Abast ID {reloaded_abastecimiento.id_abastecimiento} a: {list(recipients_data.keys())}")
            for email, (user_id, nombre) in recipients_data.items():
                await email_service.send_abastecimiento_report_email(
                    db=db, user_id_destino=user_id, email_to=email, nombre_receptor=nombre,
                    abastecimiento=reloaded_abastecimiento, pdf_content=pdf_bytes, filename=filename
                )
            print(f"-> Llamadas a send_abastecimiento_report_email completadas.")
        else:
             print(f"-> Sin destinatarios para Abast ID {reloaded_abastecimiento.id_sitio}")

    except Exception as mail_pdf_e:
        print(f"!!!!!!!! ERROR no crítico PDF/Email Abast ID {reloaded_abastecimiento.id_abastecimiento}: {mail_pdf_e} !!!!!!!!")
        print(traceback.format_exc())

    return reloaded_abastecimiento


# --- ENDPOINT GET LISTA (sin cambios) ---
@router.get("/", response_model=List[abastecimiento_schema.Abastecimiento])
# ... (código de read_abastecimientos sin cambios) ...
def read_abastecimientos(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db), current_user: models.Usuario = Depends(deps.get_current_user)):
    query = db.query(models.Abastecimiento).filter(
        models.Abastecimiento.status == 'ACTIVO'
    ).options(joinedload(models.Abastecimiento.sitio)) # Cargar sitio
    return query.order_by(
        desc(models.Abastecimiento.fecha)
    ).offset(skip).limit(limit).all()


# --- ENDPOINT ACTUALIZAR (sin cambios) ---
@router.put("/{abastecimiento_id}", response_model=abastecimiento_schema.Abastecimiento)
# ... (código de update_abastecimiento_entry sin cambios) ...
async def update_abastecimiento_entry(
    abastecimiento_id: int,
    abastecimiento_in: abastecimiento_schema.AbastecimientoUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_supervisor_or_admin_user)
):
    db_abastecimiento_base = db.get(models.Abastecimiento, abastecimiento_id)
    if not db_abastecimiento_base:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Abastecimiento con id {abastecimiento_id} no encontrado.")

    original_data = {c.name: getattr(db_abastecimiento_base, c.name) for c in db_abastecimiento_base.__table__.columns if hasattr(db_abastecimiento_base, c.name)}
    updated_abastecimiento = abastecimiento_crud.update_abastecimiento(db, db_abastecimiento=db_abastecimiento_base, abastecimiento_in=abastecimiento_in)

    reloaded_updated = db.query(models.Abastecimiento).options(
        joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.supervisor),
        joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.tecnico).joinedload(models.Tecnico.usuario)
    ).filter(models.Abastecimiento.id_abastecimiento == abastecimiento_id).first()

    if not reloaded_updated:
        print(f"Advertencia: No se pudo recargar Abast ID {abastecimiento_id} después de actualizar.")
        return updated_abastecimiento

    changes_summary = []
    update_data = abastecimiento_in.model_dump(exclude_unset=True)
    for field in update_data.keys():
        old_value = original_data.get(field)
        if hasattr(reloaded_updated, field):
            current_value = getattr(reloaded_updated, field)
            old_value_str = str(old_value.isoformat()) if isinstance(old_value, datetime) else str(old_value)
            current_value_str = str(current_value.isoformat()) if isinstance(current_value, datetime) else str(current_value)
            if current_value_str != old_value_str:
                changes_summary.append(f"<li><b>{field.replace('_', ' ').capitalize()}:</b> '{old_value}' &rarr; '{current_value}'</li>")
        else:
             print(f"Advertencia: Campo '{field}' no encontrado en objeto recargado durante la actualización.")

    if reloaded_updated.sitio and changes_summary:
        recipients_map: Dict[Optional[int], str] = {}
        site_supervisor = reloaded_updated.sitio.supervisor
        if site_supervisor and site_supervisor.correo:
             supervisor_email = site_supervisor.correo
             if supervisor_email not in recipients_map.values():
                  recipients_map[None] = supervisor_email
        site_tech = reloaded_updated.sitio.tecnico
        if site_tech and site_tech.usuario and site_tech.usuario.correo:
             technician_email = site_tech.usuario.correo
             technician_user_id = site_tech.usuario.id_usuario
             if technician_email not in recipients_map.values():
                  recipients_map[technician_user_id] = technician_email

        if recipients_map:
            try:
                await email_service.send_abastecimiento_update_notification(
                    db=db, recipients_map=recipients_map, nombre_modificador=current_user.nombre_completo,
                    modificador_email=current_user.correo, abastecimiento_id=reloaded_updated.id_abastecimiento,
                    nombre_sitio=reloaded_updated.sitio.nombre, sitio_id=reloaded_updated.sitio.id_sitio,
                    fecha_modificacion=datetime.now().strftime("%d/%m/%Y a las %H:%M:%S"),
                    changes_html="".join(changes_summary)
                )
            except Exception as e:
                 print(f"!!!!!!!! ERROR al enviar notificación de actualización para Abast ID {abastecimiento_id}: {e} !!!!!!!!")
                 print(traceback.format_exc())

    return reloaded_updated


# --- ENDPOINT ELIMINAR (sin cambios) ---
@router.delete("/{abastecimiento_id}", status_code=status.HTTP_200_OK)
# ... (código de soft_delete_abastecimiento_entry sin cambios) ...
async def soft_delete_abastecimiento_entry(
    abastecimiento_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.Usuario = Depends(deps.get_current_supervisor_or_admin_user)
):
    db_abastecimiento_loaded = db.query(models.Abastecimiento).options(
        joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.supervisor),
        joinedload(models.Abastecimiento.sitio).joinedload(models.Sitio.tecnico).joinedload(models.Tecnico.usuario)
    ).filter(models.Abastecimiento.id_abastecimiento == abastecimiento_id).first()

    if not db_abastecimiento_loaded:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Abastecimiento con id {abastecimiento_id} no encontrado.")

    recipients_map: Dict[Optional[int], str] = {}
    nombre_del_sitio = "Desconocido"

    if db_abastecimiento_loaded.sitio:
        nombre_del_sitio = db_abastecimiento_loaded.sitio.nombre
        site_supervisor = db_abastecimiento_loaded.sitio.supervisor
        if site_supervisor and site_supervisor.correo:
             supervisor_email = site_supervisor.correo
             if supervisor_email not in recipients_map.values():
                  recipients_map[None] = supervisor_email
        site_tech = db_abastecimiento_loaded.sitio.tecnico
        if site_tech and site_tech.usuario and site_tech.usuario.correo:
             technician_email = site_tech.usuario.correo
             technician_user_id = site_tech.usuario.id_usuario
             if technician_email not in recipients_map.values():
                  recipients_map[technician_user_id] = technician_email

    try:
        abastecimiento_crud.soft_delete_abastecimiento(db, db_abastecimiento=db_abastecimiento_loaded)
    except Exception as e:
         print(f"Error durante soft_delete_abastecimiento: {e}")
         print(traceback.format_exc())
         try:
             abastecimiento_base = db.get(models.Abastecimiento, abastecimiento_id)
             if abastecimiento_base:
                 abastecimiento_crud.soft_delete_abastecimiento(db, db_abastecimiento=abastecimiento_base)
             else:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado para cancelar.")
         except Exception as e2:
             print(f"Error reintentando soft_delete_abastecimiento: {e2}")
             print(traceback.format_exc())
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al cancelar el registro.")

    if recipients_map:
        try:
             await email_service.send_abastecimiento_cancellation_notification(
                db=db, recipients_map=recipients_map, nombre_cancelador=current_user.nombre_completo,
                abastecimiento_id=abastecimiento_id, nombre_sitio=nombre_del_sitio,
                fecha_cancelacion=datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
            )
        except Exception as e:
            print(f"!!!!!!!! ERROR al enviar notificación de cancelación para Abast ID {abastecimiento_id}: {e} !!!!!!!!")
            print(traceback.format_exc())

    return {"msg": f"El abastecimiento con ID {abastecimiento_id} ha sido cancelado." + (" Se ha notificado a los responsables." if recipients_map else "")}