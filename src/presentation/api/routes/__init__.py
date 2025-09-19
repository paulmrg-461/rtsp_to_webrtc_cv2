"""
Rutas de la API RTSP to WebRTC
"""

from .camera_routes import router as camera_router
from .streaming_routes import router as streaming_router

__all__ = ["camera_router", "streaming_router"]