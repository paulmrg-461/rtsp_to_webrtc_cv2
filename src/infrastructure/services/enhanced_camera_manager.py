"""
Gestor de cámaras mejorado que integra con el sistema existente
"""

import asyncio
import cv2
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from src.core.models import (
    CameraConfig, CameraStatus, CameraResponse, 
    CameraListResponse, StreamSession, CameraType
)
from src.infrastructure.services.camera_manager import CameraManager as ExistingCameraManager

logger = logging.getLogger(__name__)


class EnhancedCameraManager:
    """Gestor de cámaras mejorado con API REST"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraConfig] = {}
        self.active_streams: Dict[str, StreamSession] = {}
        self.camera_captures: Dict[str, cv2.VideoCapture] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._lock = threading.Lock()
        
        # Integración con el gestor existente
        self.existing_manager = ExistingCameraManager()
        
    async def initialize(self):
        """Inicializar el gestor"""
        try:
            await self.existing_manager.initialize()
            logger.info("EnhancedCameraManager inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando EnhancedCameraManager: {str(e)}")
            raise
        
    async def add_camera(self, camera_config: CameraConfig) -> CameraResponse:
        """Agregar una nueva cámara"""
        try:
            with self._lock:
                # Verificar si ya existe una cámara con el mismo ID
                if camera_config.id in self.cameras:
                    raise ValueError(f"Cámara con ID {camera_config.id} ya existe")
                
                # Verificar si ya existe una cámara con la misma URL
                for existing_camera in self.cameras.values():
                    if existing_camera.url == camera_config.url:
                        raise ValueError(f"Ya existe una cámara con la URL {camera_config.url}")
                
                # Agregar la cámara
                camera_config.updated_at = datetime.now()
                self.cameras[camera_config.id] = camera_config
                
                logger.info(f"Cámara agregada: {camera_config.name} ({camera_config.id})")
                
                # Intentar conectar si está habilitada
                if camera_config.enabled:
                    await self._test_camera_connection(camera_config.id)
                
                return self._camera_to_response(camera_config)
                
        except Exception as e:
            logger.error(f"Error agregando cámara: {str(e)}")
            raise
    
    async def remove_camera(self, camera_id: str) -> bool:
        """Remover una cámara"""
        try:
            with self._lock:
                if camera_id not in self.cameras:
                    return False
                
                # Detener streams activos
                await self._stop_camera_streams(camera_id)
                
                # Cerrar captura si existe
                if camera_id in self.camera_captures:
                    self.camera_captures[camera_id].release()
                    del self.camera_captures[camera_id]
                
                # Remover cámara
                camera_name = self.cameras[camera_id].name
                del self.cameras[camera_id]
                
                logger.info(f"Cámara removida: {camera_name} ({camera_id})")
                return True
                
        except Exception as e:
            logger.error(f"Error removiendo cámara {camera_id}: {str(e)}")
            return False
    
    async def update_camera(self, camera_id: str, updates: Dict[str, Any]) -> Optional[CameraResponse]:
        """Actualizar configuración de una cámara"""
        try:
            with self._lock:
                if camera_id not in self.cameras:
                    return None
                
                camera = self.cameras[camera_id]
                
                # Aplicar actualizaciones
                for key, value in updates.items():
                    if hasattr(camera, key) and value is not None:
                        setattr(camera, key, value)
                
                camera.updated_at = datetime.now()
                
                # Si se cambió la URL, reconectar
                if 'url' in updates and camera.enabled:
                    await self._test_camera_connection(camera_id)
                
                logger.info(f"Cámara actualizada: {camera.name} ({camera_id})")
                return self._camera_to_response(camera)
                
        except Exception as e:
            logger.error(f"Error actualizando cámara {camera_id}: {str(e)}")
            raise
    
    async def get_camera(self, camera_id: str) -> Optional[CameraResponse]:
        """Obtener información de una cámara"""
        camera = self.cameras.get(camera_id)
        return self._camera_to_response(camera) if camera else None
    
    async def list_cameras(self) -> CameraListResponse:
        """Listar todas las cámaras"""
        cameras = [self._camera_to_response(camera) for camera in self.cameras.values()]
        
        total = len(cameras)
        active = sum(1 for camera in cameras if camera.status == CameraStatus.ACTIVE)
        inactive = total - active
        
        return CameraListResponse(
            cameras=cameras,
            total=total,
            active=active,
            inactive=inactive
        )
    
    async def get_camera_stream(self, camera_id: str) -> Optional[cv2.VideoCapture]:
        """Obtener stream de una cámara"""
        if camera_id not in self.cameras:
            return None
        
        camera = self.cameras[camera_id]
        if not camera.enabled or camera.status != CameraStatus.ACTIVE:
            return None
        
        # Crear captura si no existe
        if camera_id not in self.camera_captures:
            await self._create_camera_capture(camera_id)
        
        return self.camera_captures.get(camera_id)
    
    async def start_stream_session(self, camera_id: str, client_id: str) -> Optional[StreamSession]:
        """Iniciar sesión de streaming"""
        if camera_id not in self.cameras:
            return None
        
        session = StreamSession(
            camera_id=camera_id,
            client_id=client_id
        )
        
        self.active_streams[session.session_id] = session
        logger.info(f"Sesión de streaming iniciada: {session.session_id} para cámara {camera_id}")
        
        return session
    
    async def stop_stream_session(self, session_id: str) -> bool:
        """Detener sesión de streaming"""
        if session_id in self.active_streams:
            session = self.active_streams[session_id]
            session.is_active = False
            del self.active_streams[session_id]
            
            logger.info(f"Sesión de streaming detenida: {session_id}")
            return True
        
        return False
    
    async def test_camera_connection(self, camera_id: str) -> bool:
        """Probar conexión con una cámara (método público)"""
        return await self._test_camera_connection(camera_id)
    
    async def get_active_sessions(self) -> List[StreamSession]:
        """Obtener sesiones activas"""
        return list(self.active_streams.values())
    
    async def _test_camera_connection(self, camera_id: str) -> bool:
        """Probar conexión con una cámara"""
        try:
            camera = self.cameras[camera_id]
            camera.status = CameraStatus.CONNECTING
            
            # Probar conexión en un hilo separado
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor, 
                self._test_connection_sync, 
                camera.url
            )
            
            camera.status = CameraStatus.ACTIVE if success else CameraStatus.ERROR
            camera.updated_at = datetime.now()
            
            return success
            
        except Exception as e:
            logger.error(f"Error probando conexión de cámara {camera_id}: {str(e)}")
            self.cameras[camera_id].status = CameraStatus.ERROR
            return False
    
    def _test_connection_sync(self, url: str) -> bool:
        """Probar conexión de forma síncrona"""
        try:
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                return ret and frame is not None
            return False
        except Exception:
            return False
    
    async def _create_camera_capture(self, camera_id: str) -> bool:
        """Crear captura de video para una cámara"""
        try:
            camera = self.cameras[camera_id]
            
            # Crear captura en un hilo separado
            loop = asyncio.get_event_loop()
            cap = await loop.run_in_executor(
                self.executor,
                cv2.VideoCapture,
                camera.url
            )
            
            if cap.isOpened():
                self.camera_captures[camera_id] = cap
                camera.status = CameraStatus.ACTIVE
                logger.info(f"Captura creada para cámara {camera_id}")
                return True
            else:
                camera.status = CameraStatus.ERROR
                return False
                
        except Exception as e:
            logger.error(f"Error creando captura para cámara {camera_id}: {str(e)}")
            self.cameras[camera_id].status = CameraStatus.ERROR
            return False
    
    async def _stop_camera_streams(self, camera_id: str):
        """Detener todos los streams de una cámara"""
        sessions_to_remove = []
        
        for session_id, session in self.active_streams.items():
            if session.camera_id == camera_id:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            await self.stop_stream_session(session_id)
    
    def _camera_to_response(self, camera: CameraConfig) -> CameraResponse:
        """Convertir CameraConfig a CameraResponse"""
        return CameraResponse(
            id=camera.id,
            name=camera.name,
            url=camera.url,
            type=camera.type,
            status=camera.status,
            location=camera.location,
            description=camera.description,
            resolution=camera.resolution,
            fps=camera.fps,
            enabled=camera.enabled,
            created_at=camera.created_at,
            updated_at=camera.updated_at,
            metadata=camera.metadata
        )
    
    async def start_existing_stream(self, camera_id: str, socketio_instance=None):
        """Iniciar stream usando el gestor existente"""
        try:
            if camera_id in self.cameras:
                camera = self.cameras[camera_id]
                # Convertir a formato del gestor existente
                existing_config = {
                    'id': camera.id,
                    'name': camera.name,
                    'rtsp_url': camera.url,
                    'enabled': camera.enabled
                }
                
                # Agregar al gestor existente si no existe
                existing_cameras = await self.existing_manager.get_cameras()
                if not any(c['id'] == camera_id for c in existing_cameras):
                    # Aquí necesitarías adaptar según la API del gestor existente
                    pass
                
                # Iniciar stream
                await self.existing_manager.start_stream(camera_id, socketio_instance)
                
                logger.info(f"Stream iniciado para cámara {camera_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error iniciando stream para cámara {camera_id}: {str(e)}")
            return False
    
    async def stop_existing_stream(self, camera_id: str):
        """Detener stream usando el gestor existente"""
        try:
            await self.existing_manager.stop_stream(camera_id)
            logger.info(f"Stream detenido para cámara {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deteniendo stream para cámara {camera_id}: {str(e)}")
            return False
    
    async def cleanup(self):
        """Limpiar recursos"""
        try:
            # Cerrar todas las capturas
            for cap in self.camera_captures.values():
                cap.release()
            
            self.camera_captures.clear()
            self.active_streams.clear()
            
            # Limpiar gestor existente
            await self.existing_manager.cleanup()
            
            # Cerrar executor
            self.executor.shutdown(wait=True)
            
            logger.info("EnhancedCameraManager limpiado correctamente")
            
        except Exception as e:
            logger.error(f"Error en cleanup de EnhancedCameraManager: {str(e)}")


# Instancia global del gestor mejorado
enhanced_camera_manager = EnhancedCameraManager()