#!/usr/bin/env python3
"""
RTSP to WebRTC API - Script de ejecución principal
"""

import asyncio
import sys
import signal
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from loguru import logger
from src.core.config import settings


def setup_logging():
    """Configurar el sistema de logging"""
    logger.remove()  # Remover el handler por defecto
    
    # Configurar formato de logs
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
    
    logger.info("Sistema de logging configurado")


def signal_handler(signum, frame):
    """Manejador de señales para cierre graceful"""
    logger.info(f"Señal {signum} recibida, cerrando aplicación...")
    sys.exit(0)


async def check_dependencies():
    """Verificar dependencias del sistema"""
    try:
        import cv2
        logger.info(f"OpenCV versión: {cv2.__version__}")
        
        # Comentado temporalmente hasta resolver problemas de instalación
        # import aiortc
        # logger.info(f"aiortc versión: {aiortc.__version__}")
        
        import socketio
        logger.info(f"python-socketio disponible")
        # logger.info(f"python-socketio versión: {socketio.__version__}")
        
        # Verificar GPU si está habilitada
        if settings.use_gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    logger.info(f"CUDA disponible: {torch.cuda.get_device_name(0)}")
                else:
                    logger.warning("CUDA no disponible, usando CPU")
            except ImportError:
                logger.warning("PyTorch no instalado, GPU no disponible")
        
        return True
        
    except ImportError as e:
        logger.error(f"Dependencia faltante: {e}")
        return False


def create_directories():
    """Crear directorios necesarios"""
    directories = [
        settings.storage_path,
        settings.logs_path,
        Path("static"),
        Path("temp")
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directorio creado/verificado: {directory}")


async def main():
    """Función principal"""
    logger.info("🎥 Iniciando RTSP to WebRTC API")
    logger.info(f"Versión: {settings.app_version}")
    logger.info(f"Entorno: {settings.environment}")
    
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Verificar dependencias
    if not await check_dependencies():
        logger.error("Faltan dependencias críticas")
        sys.exit(1)
    
    # Crear directorios
    create_directories()
    
    # Información de inicio
    logger.info(f"Servidor iniciando en http://{settings.host}:{settings.port}")
    logger.info(f"Documentación API: http://{settings.host}:{settings.port}/docs")
    logger.info(f"Demo WebRTC: http://{settings.host}:{settings.port}/")
    
    if settings.rtsp_cameras:
        logger.info(f"Cámaras RTSP configuradas: {len(settings.rtsp_cameras)}")
        for camera_id, camera_config in settings.rtsp_cameras.items():
            logger.info(f"  - {camera_id}: {camera_config.get('name', 'Sin nombre')}")
    else:
        logger.warning("No hay cámaras RTSP configuradas")
    
    # Configuración del servidor - IMPORTANTE: usar app en lugar de socket_app para que funcione lifespan
    config = uvicorn.Config(
        app="src.presentation.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True,
        loop="asyncio"
    )
    
    # Iniciar servidor
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        raise
    finally:
        logger.info("Aplicación finalizada")


if __name__ == "__main__":
    # Configurar logging
    setup_logging()
    
    try:
        # Ejecutar aplicación
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)