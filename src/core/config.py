"""
Configuración centralizada de la aplicación
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


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
    motion_threshold: int = 20
    motion_min_area: int = 300
    motion_blur_size: int = 15
    motion_detection_enabled: bool = True
    
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
    webrtc_ice_servers: List[Any] = [
        "stun:stun.l.google.com:19302",
        {"urls": ["turn:openrelay.metered.ca:80"], "username": "openrelayproject", "credential": "openrelayproject"},
        {"urls": ["turn:openrelay.metered.ca:443"], "username": "openrelayproject", "credential": "openrelayproject"},
    ]
    
    # Configuraciones adicionales del .env (opcionales)
    core_api_base_url: Optional[str] = None
    cloud_endpoint: Optional[str] = None
    local_base_url: Optional[str] = None
    site_id: Optional[str] = None
    local_postgres_db: Optional[str] = None
    local_postgres_user: Optional[str] = None
    local_postgres_password: Optional[str] = None
    local_database_url: Optional[str] = None
    email_host: Optional[str] = None
    app_email: Optional[str] = None
    app_email_password: Optional[str] = None    
    core_api_url: Optional[str] = None
    recording_disks: Optional[str] = None
    max_disk_usage_percent: Optional[str] = None
    check_interval: Optional[str] = None
    
    # Configuración de cámaras RTSP
    rtsp_cameras: Dict[str, Dict[str, Any]] = {
        "camera_1": {
        "name": "Cámara de prueba - Video local",
        "url": "/app/static/sample_video.mp4",
        "enabled": True
    },
        "camera_2": {
            "name": "Stream RTSP público - Wowza",
            "url": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
            "enabled": True
        },
        "camera_3": {
            "name": "Stream de prueba - Archivo local",
            "url": "/app/static/sample_video.mp4",
            "enabled": True
        }
    }
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )


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