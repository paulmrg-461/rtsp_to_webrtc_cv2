"""
Servicio WebRTC para streaming de video de baja latencia
Implementación real usando aiortc con hooks para procesamiento de video (YOLO)
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional, Any
import time

from src.core.config import settings

import numpy as np
from fractions import Fraction

logger = logging.getLogger(__name__)

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
    from aiortc.contrib.media import MediaRelay
    aiortc_available = True
except Exception as e:
    logger.warning(f"aiortc no disponible: {e}")
    aiortc_available = False

try:
    from av import VideoFrame
    av_available = True
except Exception as e:
    logger.warning(f"PyAV no disponible: {e}")
    av_available = False

# Añadir soporte opcional de OpenCV para procesamiento de la webcam local
try:
    import cv2
    cv2_available = True
except Exception as e:
    logger.warning(f"OpenCV no disponible: {e}")
    cv2_available = False

class WebRTCService:
    """Servicio principal de WebRTC (modo real si aiortc disponible)"""

    def __init__(self):
        self.active_connections: Dict[str, dict] = {}
        self.camera_manager = None
        self.relay = MediaRelay() if aiortc_available else None

    async def initialize(self):
        """Inicializar el servicio WebRTC"""
        if aiortc_available:
            logger.info("Inicializando servicio WebRTC (aiortc habilitado)...")
        else:
            logger.warning("WebRTC no disponible - aiortc no instalado")

    def set_camera_manager(self, camera_manager):
        """Establecer el gestor de cámaras"""
        self.camera_manager = camera_manager

    async def create_connection(self, camera_id: str) -> tuple[str, dict]:
        """Crear nueva conexión WebRTC para una cámara"""
        if not self.camera_manager:
            raise ValueError("Camera manager no configurado")

        connection_id = str(uuid.uuid4())

        if not aiortc_available:
            # Fallback: oferta simulada para validar flujo del cliente
            offer = {
                "sdp": "v=0\r\no=- 4611731400430051336 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\na=extmap-allow-mixed\r\na=msid-semantic: WMS\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\nc=IN IP4 0.0.0.0\r\na=rtcp:9 IN IP4 0.0.0.0\r\na=ice-ufrag:abcd\r\na=ice-pwd:1234567890\r\na=fingerprint:sha-256 00:00:00\r\na=setup:actpass\r\na=mid:0\r\na=sendrecv\r\na=rtpmap:96 VP8/90000\r\n",
                "type": "offer"
            }
            self.active_connections[connection_id] = {
                "connection_id": connection_id,
                "camera_id": camera_id,
                "pc": None,
                "status": "simulated",
                "created_at": time.time(),
            }
            logger.info(f"Conexión WebRTC simulada creada: {connection_id} para cámara {camera_id}")
            return connection_id, offer

        # aiortc path
        try:
            # Configurar ICE servers desde settings
            from aiortc import RTCConfiguration, RTCIceServer
            raw_ice = settings.webrtc_ice_servers if hasattr(settings, "webrtc_ice_servers") else ["stun:stun.l.google.com:19302"]
            servers = []
            for item in raw_ice:
                if isinstance(item, dict):
                    urls = item.get("urls", [])
                    username = item.get("username")
                    credential = item.get("credential")
                    servers.append(RTCIceServer(urls=urls, username=username, credential=credential))
                elif isinstance(item, str):
                    servers.append(RTCIceServer(urls=[item]))
                elif isinstance(item, list):
                    servers.append(RTCIceServer(urls=item))
            if not servers:
                servers = [RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
            config = RTCConfiguration(iceServers=servers, iceTransportPolicy="all")
            pc = RTCPeerConnection(configuration=config)
        except Exception as e:
            logger.warning(f"No se pudo aplicar configuración ICE personalizada, usando configuración por defecto: {e}")
            pc = RTCPeerConnection()
        self.active_connections[connection_id] = {
            "connection_id": connection_id,
            "camera_id": camera_id,
            "pc": pc,
            "status": "initialized",
            "created_at": time.time(),
            "queued_ice": []
        }

        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            logger.info(f"ICE state [{connection_id}]: {pc.iceConnectionState}")
            if pc.iceConnectionState in ("failed", "closed", "disconnected"):
                await self.close_connection(connection_id)

        # Prepara recepción y envío de video: el servidor enviará video procesado
        pc.addTransceiver("video", direction="sendrecv")

        # Asegurar que el stream de la cámara esté activo para generar frames
        try:
            if hasattr(self.camera_manager, "is_streaming") and not self.camera_manager.is_streaming(camera_id):
                start_res = self.camera_manager.start_stream(camera_id)
                if asyncio.iscoroutine(start_res):
                    await start_res
        except Exception as e:
            logger.warning(f"No se pudo iniciar stream para cámara {camera_id}: {e}")

        # Adjuntar track de salida con frames procesados (bounding boxes)
        if aiortc_available and av_available:
            try:
                outbound_track = OutboundCameraTrack(self.camera_manager, camera_id, fps=30)
                sender = pc.addTrack(outbound_track)
                self.active_connections[connection_id]["video_sender"] = sender
                logger.info(f"Track de salida adjuntado para cámara {camera_id}")
            except Exception as e:
                logger.error(f"Error adjuntando track de salida: {e}")

        @pc.on("track")
        async def on_track(track: MediaStreamTrack):
            logger.info(f"Track recibido [{connection_id}] kind={track.kind}")
            if track.kind == "video":
                # Si hay soporte, procesar la webcam local y reemplazar el track de salida
                if aiortc_available and av_available and cv2_available:
                    try:
                        processed_track = InboundProcessedTrack(track, fps=30)
                        conn = self.active_connections.get(connection_id, {})
                        sender = conn.get("video_sender")
                        if sender:
                            sender.replaceTrack(processed_track)
                            conn["processed_inbound"] = True
                            logger.info(f"Track de salida reemplazado por track procesado de webcam local en conexión {connection_id}")
                        else:
                            pc.addTrack(processed_track)
                            logger.info(f"Track procesado de webcam local agregado en conexión {connection_id}")
                    except Exception as e:
                        logger.error(f"Error procesando track de webcam local: {e}")
                else:
                    # TODO: Conectar este track a un pipeline de procesamiento (YOLO) y generar salida
                    # Por ahora solo mantener referencia o relé si fuese necesario
                    pass

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        logger.info(f"Conexión WebRTC creada: {connection_id} para cámara {camera_id}")
        return connection_id, {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

    async def handle_answer(self, connection_id: str, answer_data: dict):
        """Procesar respuesta del cliente"""
        conn = self.active_connections.get(connection_id)
        if not conn:
            raise ValueError(f"Conexión {connection_id} no encontrada")

        pc: Optional[RTCPeerConnection] = conn.get("pc")
        if aiortc_available and pc:
            await pc.setRemoteDescription(
                RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"]) 
            )
            logger.info(f"Respuesta WebRTC procesada para conexión {connection_id}")

            # Flush any queued ICE candidates that arrived before remoteDescription was set
            queued = conn.get("queued_ice", [])
            if queued:
                for cand in queued:
                    try:
                        from aiortc.sdp import candidate_from_sdp as _candidate_from_sdp
                        candidate_str = cand.get("candidate", "")
                        if candidate_str:
                            # Strip optional 'candidate:' prefix and parse
                            candidate_sdp = candidate_str.split(":", 1)[1] if candidate_str.startswith("candidate:") else candidate_str
                            rtc_cand = _candidate_from_sdp(candidate_sdp)
                            rtc_cand.sdpMid = cand.get("sdpMid")
                            rtc_cand.sdpMLineIndex = cand.get("sdpMLineIndex")
                            await pc.addIceCandidate(rtc_cand)
                        else:
                            # End-of-candidates marker
                            await pc.addIceCandidate(None)
                    except Exception as e:
                        logger.error(f"Error agregando ICE candidate en flush para {connection_id}: {e}")
                conn["queued_ice"] = []
        else:
            logger.info(f"Respuesta procesada (simulada) para conexión {connection_id}")

    async def add_ice_candidate(self, connection_id: str, candidate_data: dict):
        """Agregar candidato ICE a una conexión"""
        conn = self.active_connections.get(connection_id)
        if not conn:
            raise ValueError(f"Conexión {connection_id} no encontrada")

        pc: Optional[RTCPeerConnection] = conn.get("pc")
        if aiortc_available and pc:
            try:
                # If remoteDescription not set yet, queue the candidate
                if pc.remoteDescription is None:
                    conn.setdefault("queued_ice", []).append(candidate_data)
                    logger.debug(f"ICE candidate encolado (remoteDescription pendiente) para conexión {connection_id}")
                    return

                from aiortc.sdp import candidate_from_sdp as _candidate_from_sdp
                candidate_str = candidate_data.get("candidate", "")

                if candidate_str:
                    # Parse candidate from SDP string
                    candidate_sdp = candidate_str.split(":", 1)[1] if candidate_str.startswith("candidate:") else candidate_str
                    rtc_cand = _candidate_from_sdp(candidate_sdp)
                    rtc_cand.sdpMid = candidate_data.get("sdpMid")
                    rtc_cand.sdpMLineIndex = candidate_data.get("sdpMLineIndex")
                    await pc.addIceCandidate(rtc_cand)
                else:
                    # End-of-candidates
                    await pc.addIceCandidate(None)
                logger.info(f"Candidato ICE agregado correctamente para conexión {connection_id}")
            except Exception as e:
                logger.error(f"Error agregando candidato ICE para conexión {connection_id}: {e}")
        else:
            logger.debug(f"ICE candidate (simulado) para conexión {connection_id}")

    async def close_connection(self, connection_id: str):
        """Cerrar una conexión WebRTC"""
        conn = self.active_connections.pop(connection_id, None)
        if not conn:
            return

        pc: Optional[RTCPeerConnection] = conn.get("pc")
        if aiortc_available and pc:
            await pc.close()
        logger.info(f"Conexión WebRTC cerrada: {connection_id}")

    async def get_connection_stats(self, connection_id: str) -> Optional[dict]:
        """Obtener estadísticas de una conexión"""
        conn = self.active_connections.get(connection_id)
        if not conn:
            return None

        pc: Optional[RTCPeerConnection] = conn.get("pc")
        if aiortc_available and pc:
            return {
                "connection_id": connection_id,
                "connection_state": pc.connectionState,
                "ice_connection_state": pc.iceConnectionState,
                "camera_id": conn.get("camera_id"),
                "status": "aiortc activo",
            }
        else:
            return {
                "connection_id": connection_id,
                "connection_state": "simulated",
                "ice_connection_state": "simulated",
                "camera_id": conn.get("camera_id"),
                "status": "WebRTC no disponible - aiortc no instalado",
            }

    async def get_active_connections(self) -> list:
        """Obtener lista de conexiones activas"""
        connections = []
        for connection_id, conn in self.active_connections.items():
            pc: Optional[RTCPeerConnection] = conn.get("pc")
            if aiortc_available and pc:
                connections.append({
                    "connection_id": connection_id,
                    "camera_id": conn.get("camera_id"),
                    "connection_state": pc.connectionState,
                    "ice_connection_state": pc.iceConnectionState,
                    "status": "aiortc activo",
                })
            else:
                connections.append({
                    "connection_id": connection_id,
                    "camera_id": conn.get("camera_id"),
                    "connection_state": "simulated",
                    "ice_connection_state": "simulated",
                    "status": "WebRTC no disponible",
                })
        return connections

    async def cleanup(self):
        """Limpiar todas las conexiones"""
        logger.info("Limpiando servicio WebRTC...")
        for connection_id in list(self.active_connections.keys()):
            await self.close_connection(connection_id)
        logger.info("Servicio WebRTC limpiado")

# Definir track de salida solo si aiortc y PyAV están disponibles
if 'aiortc_available' in globals() and 'av_available' in globals() and aiortc_available and av_available:
    class OutboundCameraTrack(MediaStreamTrack):
        kind = "video"

        def __init__(self, camera_manager, camera_id: str, fps: int = 30):
            super().__init__()
            self.camera_manager = camera_manager
            self.camera_id = camera_id
            self.fps = fps
            self._ts = 0
            self._time_base = Fraction(1, fps)
            self._default_size = (480, 640)  # (alto, ancho) por defecto

        async def recv(self) -> VideoFrame:
            # Controlar el ritmo de salida (FPS)
            await asyncio.sleep(1 / max(1, self.fps))

            # Obtener último frame procesado (con bounding boxes) de la cámara
            result = self.camera_manager.get_camera_frame(self.camera_id)
            motion_frame = await result if asyncio.iscoroutine(result) else result

            if not motion_frame or getattr(motion_frame, "frame", None) is None:
                h, w = self._default_size
                frame_np = np.zeros((h, w, 3), dtype=np.uint8)
            else:
                frame_np = motion_frame.frame

            # Convertir a VideoFrame para WebRTC
            video_frame = VideoFrame.from_ndarray(frame_np, format="bgr24")
            self._ts += 1
            video_frame.pts = self._ts
            video_frame.time_base = self._time_base
            return video_frame

    # Track para procesar la webcam local recibida del cliente
    class InboundProcessedTrack(MediaStreamTrack):
        kind = "video"

        def __init__(self, source_track: MediaStreamTrack, fps: int = 30):
            super().__init__()
            self.source = source_track
            self.fps = fps
            self._ts = 0
            self._time_base = Fraction(1, fps)
            # Inicializar background subtractor similar al pipeline del camera_manager
            if cv2_available:
                try:
                    self._bg = cv2.createBackgroundSubtractorMOG2(
                        detectShadows=True,
                        varThreshold=16,
                        history=500,
                    )
                except Exception:
                    self._bg = None
            else:
                self._bg = None

        async def recv(self) -> VideoFrame:
            # Recibir frame de la webcam local
            frame: VideoFrame = await self.source.recv()
            img = frame.to_ndarray(format="bgr24")

            result_frame = img
            if cv2_available and self._bg is not None:
                try:
                    mask = self._bg.apply(img)
                    # Umbral dinámico configurable
                    thr = getattr(settings, "motion_threshold", 50)
                    thr = max(1, min(255, int(thr)))
                    _, th = cv2.threshold(mask, thr, 255, cv2.THRESH_BINARY)
                    # Suavizado configurable
                    kernel_size = getattr(settings, "motion_blur_size", 5)
                    if kernel_size % 2 == 0:
                        kernel_size += 1
                    th = cv2.GaussianBlur(th, (kernel_size, kernel_size), 0)
                    # Apertura para limpiar ruido + ligera dilatación para unir regiones
                    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                    th = cv2.dilate(th, np.ones((3, 3), np.uint8), iterations=1)

                    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    min_area = getattr(settings, "motion_min_area", 500)
                    motion_areas = []
                    for c in contours:
                        area = cv2.contourArea(c)
                        if area < min_area:
                            continue
                        x, y, w, h = cv2.boundingRect(c)
                        motion_areas.append((x, y, w, h))

                    if motion_areas:
                        result_frame = img.copy()
                        for x, y, w, h in motion_areas:
                            cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.putText(result_frame, "MOVIMIENTO", (x, y - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        motion_overlay = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
                        result_frame = cv2.addWeighted(result_frame, 0.8, motion_overlay, 0.2, 0)
                except Exception as e:
                    logger.debug(f"Error procesando frame de webcam local: {e}")

            # Convertir a VideoFrame para WebRTC
            video_frame = VideoFrame.from_ndarray(result_frame, format="bgr24")
            self._ts += 1
            video_frame.pts = self._ts
            video_frame.time_base = self._time_base
            return video_frame