"""
Rutas de la API para gestión de cámaras
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging

from src.core.config import settings
from src.infrastructure.services.camera_manager import CameraManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencia para obtener el camera manager
# Esto se inyectará desde main.py
camera_manager: Optional[CameraManager] = None

def get_camera_manager() -> CameraManager:
    """Obtener instancia del camera manager"""
    if camera_manager is None:
        raise HTTPException(status_code=500, detail="Camera manager no inicializado")
    return camera_manager

def set_camera_manager(cm: CameraManager):
    """Establecer instancia del camera manager"""
    global camera_manager
    camera_manager = cm

@router.get("/", response_model=List[Dict[str, Any]])
async def get_cameras(cm: CameraManager = Depends(get_camera_manager)):
    """Obtener lista de todas las cámaras disponibles"""
    try:
        cameras = await cm.get_cameras()
        return cameras
    except Exception as e:
        logger.error(f"Error obteniendo cámaras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}")
async def get_camera(camera_id: str, cm: CameraManager = Depends(get_camera_manager)):
    """Obtener información de una cámara específica"""
    try:
        cameras = await cm.get_cameras()
        camera = next((c for c in cameras if c["id"] == camera_id), None)
        
        if not camera:
            raise HTTPException(status_code=404, detail=f"Cámara {camera_id} no encontrada")
        
        return camera
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo cámara {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/start")
async def start_camera_stream(camera_id: str, cm: CameraManager = Depends(get_camera_manager)):
    """Iniciar stream de una cámara"""
    try:
        success = await cm.start_stream(camera_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"No se pudo iniciar stream de cámara {camera_id}")
        
        return {
            "message": f"Stream iniciado para cámara {camera_id}",
            "camera_id": camera_id,
            "streaming": True
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error iniciando stream de cámara {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/stop")
async def stop_camera_stream(camera_id: str, cm: CameraManager = Depends(get_camera_manager)):
    """Detener stream de una cámara"""
    try:
        success = await cm.stop_stream(camera_id)
        
        return {
            "message": f"Stream detenido para cámara {camera_id}",
            "camera_id": camera_id,
            "streaming": False
        }
    except Exception as e:
        logger.error(f"Error deteniendo stream de cámara {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/status")
async def get_camera_status(camera_id: str, cm: CameraManager = Depends(get_camera_manager)):
    """Obtener estado actual de una cámara"""
    try:
        cameras = await cm.get_cameras()
        camera = next((c for c in cameras if c["id"] == camera_id), None)
        
        if not camera:
            raise HTTPException(status_code=404, detail=f"Cámara {camera_id} no encontrada")
        
        # Obtener frame más reciente si está streaming
        latest_frame = None
        if camera["streaming"]:
            motion_frame = await cm.get_camera_frame(camera_id)
            if motion_frame:
                latest_frame = {
                    "motion_detected": motion_frame.motion_detected,
                    "motion_areas": motion_frame.motion_areas,
                    "timestamp": motion_frame.timestamp
                }
        
        return {
            "camera_id": camera_id,
            "name": camera["name"],
            "enabled": camera["enabled"],
            "streaming": camera["streaming"],
            "width": camera["width"],
            "height": camera["height"],
            "fps": camera["fps"],
            "latest_frame": latest_frame
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado de cámara {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/frame")
async def get_camera_frame(camera_id: str, cm: CameraManager = Depends(get_camera_manager)):
    """Obtener el frame más reciente de una cámara (solo metadatos, no imagen)"""
    try:
        motion_frame = await cm.get_camera_frame(camera_id)
        
        if not motion_frame:
            raise HTTPException(status_code=404, detail=f"No hay frames disponibles para cámara {camera_id}")
        
        return {
            "camera_id": camera_id,
            "motion_detected": motion_frame.motion_detected,
            "motion_areas": motion_frame.motion_areas,
            "timestamp": motion_frame.timestamp,
            "frame_shape": motion_frame.frame.shape if motion_frame.frame is not None else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo frame de cámara {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))