"""
Rutas de la API para gestión de streaming WebRTC
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from src.infrastructure.services.webrtc_service import WebRTCService

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencia para obtener el WebRTC service
# Esto se inyectará desde main.py
webrtc_service: Optional[WebRTCService] = None

def get_webrtc_service() -> WebRTCService:
    """Obtener instancia del WebRTC service"""
    if webrtc_service is None:
        raise HTTPException(status_code=500, detail="WebRTC service no inicializado")
    return webrtc_service

def set_webrtc_service(ws: WebRTCService):
    """Establecer instancia del WebRTC service"""
    global webrtc_service
    webrtc_service = ws

# Modelos Pydantic para requests
class WebRTCOfferRequest(BaseModel):
    camera_id: str

class WebRTCAnswerRequest(BaseModel):
    connection_id: str
    sdp: str
    type: str

class ICECandidateRequest(BaseModel):
    connection_id: str
    candidate: Dict[str, Any]

@router.post("/webrtc/offer")
async def create_webrtc_offer(
    request: WebRTCOfferRequest,
    ws: WebRTCService = Depends(get_webrtc_service)
):
    """Crear oferta WebRTC para una cámara específica"""
    try:
        connection_id, offer = await ws.create_connection(request.camera_id)
        
        return {
            "connection_id": connection_id,
            "camera_id": request.camera_id,
            "offer": offer
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando oferta WebRTC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webrtc/answer")
async def handle_webrtc_answer(
    request: WebRTCAnswerRequest,
    ws: WebRTCService = Depends(get_webrtc_service)
):
    """Manejar respuesta WebRTC del cliente"""
    try:
        answer_data = {
            "sdp": request.sdp,
            "type": request.type
        }
        
        await ws.handle_answer(request.connection_id, answer_data)
        
        return {
            "message": "Respuesta WebRTC procesada correctamente",
            "connection_id": request.connection_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error procesando respuesta WebRTC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webrtc/ice-candidate")
async def add_ice_candidate(
    request: ICECandidateRequest,
    ws: WebRTCService = Depends(get_webrtc_service)
):
    """Agregar candidato ICE a una conexión WebRTC"""
    try:
        await ws.add_ice_candidate(request.connection_id, request.candidate)
        
        return {
            "message": "Candidato ICE agregado correctamente",
            "connection_id": request.connection_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error agregando candidato ICE: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webrtc/{connection_id}")
async def close_webrtc_connection(
    connection_id: str,
    ws: WebRTCService = Depends(get_webrtc_service)
):
    """Cerrar una conexión WebRTC"""
    try:
        await ws.close_connection(connection_id)
        
        return {
            "message": f"Conexión WebRTC {connection_id} cerrada correctamente",
            "connection_id": connection_id
        }
    except Exception as e:
        logger.error(f"Error cerrando conexión WebRTC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webrtc/{connection_id}/stats")
async def get_webrtc_stats(
    connection_id: str,
    ws: WebRTCService = Depends(get_webrtc_service)
):
    """Obtener estadísticas de una conexión WebRTC"""
    try:
        stats = await ws.get_connection_stats(connection_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail=f"Conexión {connection_id} no encontrada")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas WebRTC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webrtc/connections")
async def get_active_connections(ws: WebRTCService = Depends(get_webrtc_service)):
    """Obtener lista de conexiones WebRTC activas"""
    try:
        connections = await ws.get_active_connections()
        
        return {
            "active_connections": len(connections),
            "connections": connections
        }
    except Exception as e:
        logger.error(f"Error obteniendo conexiones activas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def streaming_health_check(ws: WebRTCService = Depends(get_webrtc_service)):
    """Health check específico para el servicio de streaming"""
    try:
        connections = await ws.get_active_connections()
        
        return {
            "status": "healthy",
            "service": "streaming",
            "active_connections": len(connections),
            "webrtc_enabled": True
        }
    except Exception as e:
        logger.error(f"Error en health check de streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))