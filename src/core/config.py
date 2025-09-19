"""
Configuración centralizada de la aplicación
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings"""
    
    # Aplicación
    app_name: str = "RTSP to WebRTC Streaming API"
    app_version: str = "1.0.0"
    environment: str = "production"
    
    # Servidor
    host: str = "0.0.0.0"
    port: int = 8990
    
    # Detección de Movimiento
    motion_threshold: int = 25
    motion_min_area: int = 500
    motion_blur_size: int = 21
    
    # Video
    video_width: int = 640
    video_height: int = 480
    video_fps: int = 30
    
    # GPU
    use_gpu: bool = False
    gpu_device_id: int = 0
    
    # Directorios
    storage_path: str = "./storage"
    logs_path: str = "./logs"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/app.log"
    
    # Seguridad
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_origins: List[str] = ["*"]
    
    # Socket.IO
    socketio_cors_origins: List[str] = ["*"]
    socketio_async_mode: str = "asgi"
    
    # WebRTC
    webrtc_ice_servers: List[str] = ["stun:stun.l.google.com:19302"]
    
    # Cámaras RTSP por defecto
    rtsp_cameras: Dict[str, Dict[str, Any]] = {
        "camera_1": {
            "name": "Cámara de Prueba",
            "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
            "enabled": True
        }
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()


def setup_logging():
    """Configurar el sistema de logging usando loguru"""
    from loguru import logger
    import sys
    
    # Remover el handler por defecto
    logger.remove()
    
    # Formato de logs
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Log a consola
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Log a archivo si está configurado
    if settings.log_file:
        # Crear directorio de logs si no existe
        Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.log_file,
            format=log_format,
            level=settings.log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    return logger