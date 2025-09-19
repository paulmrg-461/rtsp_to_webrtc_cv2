"""
Servicio WebRTC para streaming de video de baja latencia
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional, Set, Any
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
import fractions
import time

from src.core.config import settings
from src.infrastructure.services.camera_manager import MotionFrame

logger = logging.getLogger(__name__)

class CameraVideoTrack(VideoStreamTrack):
    """Track de video personalizado para cámaras RTSP"""
    
    def __init__(self, camera_manager, camera_id: str):
        super().__init__()
        self.camera_manager = camera_manager
        self.camera_id = camera_id
        self.kind = "video"
        
    async def recv(self):
        """Recibir el siguiente frame de video"""
        try:
            # Obtener frame más reciente de la cámara
            motion_frame = await self.camera_manager.get_camera_frame(self.camera_id)
            
            if motion_frame is None:
                # Si no hay frame, crear uno negro
                frame = np.zeros((settings.video_height, settings.video_width, 3), dtype=np.uint8)
                cv2.putText(frame, "No Signal", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                frame = motion_frame.frame
            
            # Redimensionar si es necesario
            if frame.shape[:2] != (settings.video_height, settings.video_width):
                frame = cv2.resize(frame, (settings.video_width, settings.video_height))
            
            # Convertir BGR a RGB (OpenCV usa BGR, WebRTC usa RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Crear frame de aiortc
            from av import VideoFrame
            av_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
            av_frame.pts = int(time.time() * 1000000)  # timestamp en microsegundos
            av_frame.time_base = fractions.Fraction(1, 1000000)
            
            return av_frame
            
        except Exception as e:
            logger.error(f"Error en CameraVideoTrack.recv: {e}")
            # Retornar frame negro en caso de error
            frame = np.zeros((settings.video_height, settings.video_width, 3), dtype=np.uint8)
            cv2.putText(frame, "Error", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            from av import VideoFrame
            av_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            av_frame.pts = int(time.time() * 1000000)
            av_frame.time_base = fractions.Fraction(1, 1000000)
            
            return av_frame

class WebRTCConnection:
    """Conexión WebRTC individual"""
    
    def __init__(self, connection_id: str, camera_manager):
        self.connection_id = connection_id
        self.camera_manager = camera_manager
        self.pc = RTCPeerConnection(configuration={
            "iceServers": [{"urls": server} for server in settings.webrtc_stun_servers]
        })
        self.video_track: Optional[CameraVideoTrack] = None
        self.camera_id: Optional[str] = None
        
        # Configurar eventos
        self._setup_events()
    
    def _setup_events(self):
        """Configurar eventos de la conexión WebRTC"""
        
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Conexión {self.connection_id} cambió a estado: {self.pc.connectionState}")
            
            if self.pc.connectionState == "closed":
                await self.cleanup()
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE conexión {self.connection_id} cambió a estado: {self.pc.iceConnectionState}")
    
    async def create_offer(self, camera_id: str) -> dict:
        """Crear oferta WebRTC para una cámara específica"""
        try:
            self.camera_id = camera_id
            
            # Crear track de video para la cámara
            self.video_track = CameraVideoTrack(self.camera_manager, camera_id)
            self.pc.addTrack(self.video_track)
            
            # Crear oferta
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            return {
                "sdp": self.pc.localDescription.sdp,
                "type": self.pc.localDescription.type
            }
            
        except Exception as e:
            logger.error(f"Error creando oferta WebRTC: {e}")
            raise
    
    async def handle_answer(self, answer_data: dict):
        """Manejar respuesta WebRTC del cliente"""
        try:
            answer = RTCSessionDescription(
                sdp=answer_data["sdp"],
                type=answer_data["type"]
            )
            await self.pc.setRemoteDescription(answer)
            
        except Exception as e:
            logger.error(f"Error manejando respuesta WebRTC: {e}")
            raise
    
    async def add_ice_candidate(self, candidate_data: dict):
        """Agregar candidato ICE"""
        try:
            from aiortc import RTCIceCandidate
            candidate = RTCIceCandidate(
                component=candidate_data.get("component"),
                foundation=candidate_data.get("foundation"),
                ip=candidate_data.get("ip"),
                port=candidate_data.get("port"),
                priority=candidate_data.get("priority"),
                protocol=candidate_data.get("protocol"),
                type=candidate_data.get("type")
            )
            await self.pc.addIceCandidate(candidate)
            
        except Exception as e:
            logger.error(f"Error agregando candidato ICE: {e}")
            raise
    
    async def cleanup(self):
        """Limpiar recursos de la conexión"""
        try:
            if self.pc.connectionState != "closed":
                await self.pc.close()
            
            if self.video_track:
                self.video_track = None
                
        except Exception as e:
            logger.error(f"Error limpiando conexión WebRTC: {e}")

class WebRTCService:
    """Servicio principal de WebRTC"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebRTCConnection] = {}
        self.camera_manager = None
        
    async def initialize(self):
        """Inicializar el servicio WebRTC"""
        logger.info("Inicializando servicio WebRTC...")
        # El camera_manager se inyectará desde main.py
        logger.info("Servicio WebRTC inicializado")
    
    def set_camera_manager(self, camera_manager):
        """Establecer el gestor de cámaras"""
        self.camera_manager = camera_manager
    
    async def create_connection(self, camera_id: str) -> tuple[str, dict]:
        """Crear nueva conexión WebRTC para una cámara"""
        if not self.camera_manager:
            raise ValueError("Camera manager no configurado")
        
        connection_id = str(uuid.uuid4())
        connection = WebRTCConnection(connection_id, self.camera_manager)
        
        try:
            # Crear oferta
            offer = await connection.create_offer(camera_id)
            
            # Guardar conexión
            self.active_connections[connection_id] = connection
            
            logger.info(f"Conexión WebRTC creada: {connection_id} para cámara {camera_id}")
            
            return connection_id, offer
            
        except Exception as e:
            logger.error(f"Error creando conexión WebRTC: {e}")
            await connection.cleanup()
            raise
    
    async def handle_answer(self, connection_id: str, answer_data: dict):
        """Manejar respuesta del cliente"""
        if connection_id not in self.active_connections:
            raise ValueError(f"Conexión {connection_id} no encontrada")
        
        connection = self.active_connections[connection_id]
        await connection.handle_answer(answer_data)
        
        logger.info(f"Respuesta WebRTC procesada para conexión {connection_id}")
    
    async def add_ice_candidate(self, connection_id: str, candidate_data: dict):
        """Agregar candidato ICE a una conexión"""
        if connection_id not in self.active_connections:
            raise ValueError(f"Conexión {connection_id} no encontrada")
        
        connection = self.active_connections[connection_id]
        await connection.add_ice_candidate(candidate_data)
    
    async def close_connection(self, connection_id: str):
        """Cerrar una conexión WebRTC"""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            await connection.cleanup()
            del self.active_connections[connection_id]
            
            logger.info(f"Conexión WebRTC cerrada: {connection_id}")
    
    async def get_connection_stats(self, connection_id: str) -> Optional[dict]:
        """Obtener estadísticas de una conexión"""
        if connection_id not in self.active_connections:
            return None
        
        connection = self.active_connections[connection_id]
        
        try:
            stats = await connection.pc.getStats()
            return {
                "connection_id": connection_id,
                "connection_state": connection.pc.connectionState,
                "ice_connection_state": connection.pc.iceConnectionState,
                "camera_id": connection.camera_id,
                "stats": stats
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None
    
    async def get_active_connections(self) -> list:
        """Obtener lista de conexiones activas"""
        connections = []
        for connection_id, connection in self.active_connections.items():
            connections.append({
                "connection_id": connection_id,
                "camera_id": connection.camera_id,
                "connection_state": connection.pc.connectionState,
                "ice_connection_state": connection.pc.iceConnectionState
            })
        return connections
    
    async def cleanup(self):
        """Limpiar todas las conexiones"""
        logger.info("Limpiando servicio WebRTC...")
        
        # Cerrar todas las conexiones
        for connection_id in list(self.active_connections.keys()):
            await self.close_connection(connection_id)
        
        logger.info("Servicio WebRTC limpiado")