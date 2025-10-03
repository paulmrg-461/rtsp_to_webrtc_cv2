"""
Servicio de gestión de cámaras RTSP con detección de movimiento
"""

import cv2
import numpy as np
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import base64

from src.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class CameraConfig:
    """Configuración de una cámara"""
    id: str
    name: str
    rtsp_url: str
    enabled: bool = True
    width: int = 640
    height: int = 480
    fps: int = 30

@dataclass
class MotionFrame:
    """Frame con información de movimiento detectado"""
    frame: np.ndarray
    motion_mask: np.ndarray
    motion_detected: bool
    motion_areas: List[tuple]
    timestamp: float

class RTSPCameraStream:
    """Stream de una cámara RTSP individual"""
    
    def __init__(self, config: CameraConfig):
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.background_subtractor = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.latest_frame: Optional[MotionFrame] = None
        self.frame_lock = threading.Lock()
        self.subscribers: List[Any] = []
        
        # Configuración de detección de movimiento
        self.motion_threshold = settings.motion_threshold
        self.blur_size = settings.motion_blur_size
        self.min_area = settings.motion_min_area
        
    async def initialize(self):
        """Inicializar la cámara y el detector de movimiento"""
        try:
            logger.info(f"🔧 Inicializando cámara {self.config.id}: {self.config.name}")
            logger.info(f"🌐 URL: {self.config.rtsp_url}")
            
            # Crear captura de video con configuración optimizada
            self.cap = cv2.VideoCapture()
            
            # Configurar backend específico según el tipo de URL
            if self.config.rtsp_url.startswith('rtsp://'):
                # Para streams RTSP, usar FFmpeg
                logger.info(f"🎬 Usando backend FFmpeg para RTSP: {self.config.rtsp_url}")
                self.cap.open(self.config.rtsp_url, cv2.CAP_FFMPEG)
            elif self.config.rtsp_url.isdigit():
                # Para dispositivos locales, usar V4L2 en Linux
                device_id = int(self.config.rtsp_url)
                logger.info(f"📹 Usando backend V4L2 para dispositivo local: {device_id}")
                self.cap.open(device_id, cv2.CAP_V4L2)
            elif self.config.rtsp_url.startswith('/dev/video'):
                # Para dispositivos de video específicos
                logger.info(f"📹 Usando backend V4L2 para dispositivo: {self.config.rtsp_url}")
                self.cap.open(self.config.rtsp_url, cv2.CAP_V4L2)
            else:
                # Fallback a backend por defecto
                logger.info(f"🔄 Usando backend por defecto para: {self.config.rtsp_url}")
                self.cap.open(self.config.rtsp_url)
            
            # Configurar propiedades optimizadas para RTSP
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Configuración optimizada de buffer para RTSP
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo para baja latencia
            
            # Configuraciones adicionales para FFmpeg backend
            if hasattr(cv2, 'CAP_PROP_FOURCC'):
                # Forzar codec H.264 si está disponible
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            
            # Configurar timeout para conexiones RTSP
            if hasattr(cv2, 'CAP_PROP_OPEN_TIMEOUT_MSEC'):
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 30000)  # 30 segundos timeout
            
            if hasattr(cv2, 'CAP_PROP_READ_TIMEOUT_MSEC'):
                self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)   # 5 segundos read timeout
            
            # Verificar conexión
            logger.info(f"🔍 Verificando conexión para cámara {self.config.id}...")
            if not self.cap.isOpened():
                raise Exception(f"No se pudo conectar a la cámara: {self.config.rtsp_url}")
            
            # Intentar leer un frame para verificar que funciona
            ret, frame = self.cap.read()
            if not ret or frame is None:
                raise Exception(f"No se pudo leer frame de la cámara: {self.config.rtsp_url}")
            
            logger.info(f"📏 Frame leído exitosamente: {frame.shape}")
            
            # Inicializar detector de movimiento
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True,
                varThreshold=16,
                history=500
            )
            
            logger.info(f"✅ Cámara {self.config.id} inicializada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando cámara {self.config.id}: {e}")
            logger.error(f"🔧 Detalles del error: {type(e).__name__}")
            return False
    
    def start_stream(self):
        """Iniciar el stream de la cámara"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Stream iniciado para cámara {self.config.id}")
    
    def stop_stream(self):
        """Detener el stream de la cámara"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info(f"Stream detenido para cámara {self.config.id}")
    
    def _capture_loop(self):
        """Loop principal de captura de video optimizado para RTSP"""
        frame_time = 1.0 / self.config.fps
        consecutive_failures = 0
        max_failures = 10
        
        while self.is_running and self.cap and self.cap.isOpened():
            start_time = time.time()
            
            try:
                # Limpiar buffer para obtener el frame más reciente (reduce latencia)
                # Esto es especialmente importante para streams RTSP en tiempo real
                buffer_size = int(self.cap.get(cv2.CAP_PROP_BUFFERSIZE))
                for _ in range(buffer_size):
                    self.cap.grab()
                
                ret, frame = self.cap.retrieve()
                if not ret:
                    consecutive_failures += 1
                    logger.warning(f"No se pudo leer frame de cámara {self.config.id} (fallos consecutivos: {consecutive_failures})")
                    
                    if consecutive_failures >= max_failures:
                        logger.error(f"Demasiados fallos consecutivos en cámara {self.config.id}, intentando reconectar...")
                        # Ejecutar reconexión en un hilo separado para no bloquear
                        threading.Thread(target=self._sync_reconnect, daemon=True).start()
                        consecutive_failures = 0
                    
                    time.sleep(0.1)
                    continue
                
                # Reset contador de fallos en lectura exitosa
                consecutive_failures = 0
                
                # Verificar calidad del frame
                if frame is None or frame.size == 0:
                    logger.warning(f"Frame vacío o corrupto de cámara {self.config.id}")
                    continue
                
                # Procesar detección de movimiento
                motion_frame = self._process_motion_detection(frame)
                
                # Actualizar frame más reciente
                with self.frame_lock:
                    self.latest_frame = motion_frame
                
                # Notificar a suscriptores
                self._notify_subscribers(motion_frame)
                
                # Control de FPS adaptativo
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error en loop de captura para cámara {self.config.id}: {e}")
                
                if consecutive_failures >= max_failures:
                    logger.error(f"Demasiados errores consecutivos en cámara {self.config.id}, intentando reconectar...")
                    # Ejecutar reconexión en un hilo separado para no bloquear
                    threading.Thread(target=self._sync_reconnect, daemon=True).start()
                    consecutive_failures = 0
                
                time.sleep(1)
    
    def _sync_reconnect(self):
        """Wrapper síncrono para la reconexión asíncrona"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._reconnect())
        except Exception as e:
            logger.error(f"Error en reconexión síncrona para cámara {self.config.id}: {e}")
        finally:
            loop.close()
    
    async def _reconnect(self):
        """Reconectar la cámara RTSP en caso de fallos"""
        try:
            logger.info(f"Intentando reconectar cámara {self.config.id}...")
            
            # Cerrar conexión actual
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # Esperar antes de reconectar
            await asyncio.sleep(2)
            
            # Reinicializar la conexión
            await self.initialize()
            
            if self.cap and self.cap.isOpened():
                logger.info(f"Reconexión exitosa para cámara {self.config.id}")
            else:
                logger.error(f"Falló la reconexión para cámara {self.config.id}")
                
        except Exception as e:
            logger.error(f"Error durante reconexión de cámara {self.config.id}: {e}")
    
    def _process_motion_detection(self, frame: np.ndarray) -> MotionFrame:
        """Procesar detección de movimiento en el frame"""
        timestamp = time.time()
        
        if not settings.motion_detection_enabled:
            return MotionFrame(
                frame=frame,
                motion_mask=np.zeros(frame.shape[:2], dtype=np.uint8),
                motion_detected=False,
                motion_areas=[],
                timestamp=timestamp
            )
        
        try:
            # Aplicar sustractor de fondo
            motion_mask = self.background_subtractor.apply(frame)
            
            # Aplicar filtros para reducir ruido
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
            motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_CLOSE, kernel)
            
            # Aplicar blur gaussiano
            motion_mask = cv2.GaussianBlur(motion_mask, (self.blur_size, self.blur_size), 0)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtrar contornos por área mínima
            motion_areas = []
            motion_detected = False
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_area:
                    motion_detected = True
                    x, y, w, h = cv2.boundingRect(contour)
                    motion_areas.append((x, y, w, h))
            
            # Dibujar overlay de movimiento en el frame
            result_frame = frame.copy()
            if motion_detected:
                # Dibujar rectángulos de movimiento
                for x, y, w, h in motion_areas:
                    cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(result_frame, "MOVIMIENTO", (x, y - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Overlay de máscara de movimiento (semi-transparente)
                motion_overlay = cv2.applyColorMap(motion_mask, cv2.COLORMAP_JET)
                result_frame = cv2.addWeighted(result_frame, 0.8, motion_overlay, 0.2, 0)
            
            return MotionFrame(
                frame=result_frame,
                motion_mask=motion_mask,
                motion_detected=motion_detected,
                motion_areas=motion_areas,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error en detección de movimiento para cámara {self.config.id}: {e}")
            return MotionFrame(
                frame=frame,
                motion_mask=np.zeros(frame.shape[:2], dtype=np.uint8),
                motion_detected=False,
                motion_areas=[],
                timestamp=timestamp
            )
    
    def _notify_subscribers(self, motion_frame: MotionFrame):
        """Notificar a los suscriptores sobre el nuevo frame"""
        for subscriber in self.subscribers[:]:  # Copia para evitar modificaciones concurrentes
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    # Para funciones async, programar la ejecución
                    asyncio.create_task(subscriber(self.config.id, motion_frame))
                else:
                    # Para funciones síncronas
                    subscriber(self.config.id, motion_frame)
            except Exception as e:
                logger.error(f"Error notificando suscriptor: {e}")
                # Remover suscriptor problemático
                if subscriber in self.subscribers:
                    self.subscribers.remove(subscriber)
    
    def subscribe(self, callback):
        """Suscribirse a los frames de la cámara"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
    
    def unsubscribe(self, callback):
        """Desuscribirse de los frames de la cámara"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_latest_frame(self) -> Optional[MotionFrame]:
        """Obtener el frame más reciente"""
        with self.frame_lock:
            return self.latest_frame
    
    def cleanup(self):
        """Limpiar recursos"""
        self.stop_stream()
        if self.cap:
            self.cap.release()
        self.subscribers.clear()

class CameraManager:
    """Gestor principal de cámaras"""
    
    def __init__(self):
        self.cameras: Dict[str, RTSPCameraStream] = {}
        self.active_streams: Dict[str, RTSPCameraStream] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """Inicializar el gestor de cámaras"""
        logger.info("🔄 INICIANDO GESTOR DE CÁMARAS...")
        logger.info(f"📋 Configuración de cámaras RTSP: {settings.rtsp_cameras}")
        
        # Cargar configuración de cámaras
        for camera_id, camera_config in settings.rtsp_cameras.items():
            logger.info(f"🔍 Procesando cámara {camera_id}: {camera_config}")
            
            # Solo procesar cámaras habilitadas
            if not camera_config.get("enabled", True):
                logger.info(f"⏭️ Cámara {camera_id} está deshabilitada, omitiendo...")
                continue
            
            # Mapear los campos de configuración a los esperados por CameraConfig
            config_data = {
                "id": camera_id,
                "name": camera_config.get("name", f"Cámara {camera_id}"),
                "rtsp_url": camera_config.get("url"),  # Mapear 'url' a 'rtsp_url'
                "enabled": camera_config.get("enabled", True)
            }
            logger.info(f"📝 Datos de configuración mapeados: {config_data}")
            
            config = CameraConfig(**config_data)
            camera_stream = RTSPCameraStream(config)
            
            # Inicializar cámara
            logger.info(f"🚀 Intentando inicializar cámara {config.id}...")
            if await camera_stream.initialize():
                self.cameras[config.id] = camera_stream
                logger.info(f"✅ Cámara {config.id} agregada al gestor exitosamente")
            else:
                logger.error(f"❌ No se pudo inicializar cámara {config.id}")
        
        logger.info(f"🎯 Gestor de cámaras inicializado con {len(self.cameras)} cámaras")
        logger.info(f"📹 Cámaras disponibles: {list(self.cameras.keys())}")
        
        # Log adicional para debug
        if len(self.cameras) == 0:
            logger.warning("⚠️ NO SE INICIALIZÓ NINGUNA CÁMARA - Verificar configuración y conectividad")
    
    async def start_stream(self, camera_id: str, socketio_instance=None):
        """Iniciar stream de una cámara"""
        if camera_id not in self.cameras:
            raise ValueError(f"Cámara {camera_id} no encontrada")
        
        camera = self.cameras[camera_id]
        
        if camera_id not in self.active_streams:
            # Suscribirse a los frames para envío por Socket.IO
            if socketio_instance:
                camera.subscribe(lambda cid, frame: self._send_frame_socketio(cid, frame, socketio_instance))
            
            camera.start_stream()
            self.active_streams[camera_id] = camera
            logger.info(f"Stream iniciado para cámara {camera_id}")
        
        return True
    
    async def stop_stream(self, camera_id: str):
        """Detener stream de una cámara"""
        if camera_id in self.active_streams:
            camera = self.active_streams[camera_id]
            camera.stop_stream()
            del self.active_streams[camera_id]
            logger.info(f"Stream detenido para cámara {camera_id}")
        
        return True
    
    def is_streaming(self, camera_id: str) -> bool:
        """Verificar si una cámara está streaming"""
        return camera_id in self.active_streams
    
    async def get_cameras(self) -> List[Dict[str, Any]]:
        """Obtener lista de cámaras disponibles"""
        cameras = []
        for camera_id, camera in self.cameras.items():
            cameras.append({
                "id": camera_id,
                "name": camera.config.name,
                "enabled": camera.config.enabled,
                "streaming": self.is_streaming(camera_id),
                "width": camera.config.width,
                "height": camera.config.height,
                "fps": camera.config.fps
            })
        return cameras
    
    async def get_camera_frame(self, camera_id: str) -> Optional[MotionFrame]:
        """Obtener el frame más reciente de una cámara"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_latest_frame()
        return None
    
    async def cleanup_client(self, client_id: str):
        """Limpiar recursos de un cliente específico"""
        # Implementar lógica de limpieza por cliente si es necesario
        pass
    
    async def cleanup(self):
        """Limpiar todos los recursos"""
        logger.info("Limpiando gestor de cámaras...")
        
        # Detener todos los streams
        for camera_id in list(self.active_streams.keys()):
            await self.stop_stream(camera_id)
        
        # Limpiar todas las cámaras
        for camera in self.cameras.values():
            camera.cleanup()
        
        self.cameras.clear()
        self.executor.shutdown(wait=True)
        logger.info("Gestor de cámaras limpiado")
    
    async def _send_frame_socketio(self, camera_id: str, motion_frame: MotionFrame, socketio_instance):
        """Enviar frame a través de Socket.IO"""
        try:
            # Codificar frame como JPEG
            _, buffer = cv2.imencode('.jpg', motion_frame.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Preparar datos del frame
            frame_data = {
                "camera_id": camera_id,
                "frame": frame_base64,
                "motion_detected": motion_frame.motion_detected,
                "motion_areas": motion_frame.motion_areas,
                "timestamp": motion_frame.timestamp
            }
            
            # Enviar a todos los clientes suscritos a esta cámara
            await socketio_instance.emit('video_frame', frame_data, room=f"camera_{camera_id}")
            
        except Exception as e:
            logger.error(f"Error enviando frame por Socket.IO: {e}")