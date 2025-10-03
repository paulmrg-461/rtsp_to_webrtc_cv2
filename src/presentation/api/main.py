"""
RTSP to WebRTC API Main Application
Aplicación principal para streaming de video RTSP con detección de movimiento y transmisión WebRTC
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socketio
import uvicorn
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from src.core.config import settings
from src.presentation.api.routes import camera_router, streaming_router
from src.presentation.api.routes.camera_routes import set_camera_manager
from src.presentation.api.routes.streaming_routes import set_webrtc_service
from src.infrastructure.services.enhanced_camera_manager import enhanced_camera_manager
from src.infrastructure.services.webrtc_service import WebRTCService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instancias globales
camera_manager = enhanced_camera_manager  # Usar el gestor mejorado
webrtc_service = WebRTCService()

# Configurar Socket.IO
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
    logger=True,
    engineio_logger=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Inicialización
    logger.info("🚀 LIFESPAN: Iniciando ciclo de vida de FastAPI")
    logger.info("🔄 LIFESPAN: Inicializando servicios...")
    
    # Inicializar el gestor de cámaras
    logger.info("📋 LIFESPAN: Inicializando camera_manager...")
    await camera_manager.initialize()
    logger.info("✅ LIFESPAN: camera_manager inicializado")
    
    # Inicializar el servicio WebRTC
    logger.info("📋 LIFESPAN: Inicializando webrtc_service...")
    await webrtc_service.initialize()
    logger.info("✅ LIFESPAN: webrtc_service inicializado")
    
    # Configurar dependencias
    logger.info("📋 LIFESPAN: Configurando dependencias...")
    webrtc_service.set_camera_manager(camera_manager)
    set_camera_manager(camera_manager)
    set_webrtc_service(webrtc_service)
    
    logger.info("✅ LIFESPAN: Servicios inicializados correctamente")
    
    yield
    
    # Limpieza
    logger.info("🔄 LIFESPAN: Cerrando servicios...")
    await camera_manager.cleanup()
    await webrtc_service.cleanup()
    logger.info("✅ LIFESPAN: Servicios cerrados")

# Crear aplicación FastAPI
app = FastAPI(
    title="RTSP to WebRTC API",
    description="API para streaming de video RTSP con detección de movimiento y transmisión WebRTC",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(camera_router, prefix="/api/cameras", tags=["cameras"])
app.include_router(streaming_router, prefix="/api/streaming", tags=["streaming"])

# Incluir nuevos endpoints de gestión de cámaras
from src.api.endpoints.cameras import router as cameras_api_router
app.include_router(cameras_api_router, prefix="/api/v2")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta raíz que sirve el index.html
@app.get("/")
async def serve_index():
    """Servir la página principal"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

# Eventos Socket.IO
@sio.event
async def connect(sid, environ):
    """Cliente conectado"""
    logger.info(f"Cliente conectado: {sid}")
    await sio.emit('connected', {'message': 'Conectado al servidor RTSP to WebRTC'}, room=sid)

@sio.event
async def disconnect(sid):
    """Cliente desconectado"""
    logger.info(f"Cliente desconectado: {sid}")
    # Limpiar recursos del cliente
    await camera_manager.cleanup_client(sid)

@sio.event
async def join_camera_stream(sid, data):
    """Unirse al stream de una cámara"""
    try:
        camera_id = data.get('camera_id')
        if not camera_id:
            await sio.emit('error', {'message': 'camera_id requerido'}, room=sid)
            return
        
        # Unirse al room de la cámara
        await sio.enter_room(sid, f"camera_{camera_id}")
        
        # Iniciar stream si no está activo
        if not camera_manager.is_streaming(camera_id):
            await camera_manager.start_stream(camera_id, sio)
        
        await sio.emit('joined_stream', {
            'camera_id': camera_id,
            'message': f'Unido al stream de la cámara {camera_id}'
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Error al unirse al stream: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def leave_camera_stream(sid, data):
    """Salir del stream de una cámara"""
    try:
        camera_id = data.get('camera_id')
        if not camera_id:
            await sio.emit('error', {'message': 'camera_id requerido'}, room=sid)
            return
        
        # Salir del room de la cámara
        await sio.leave_room(sid, f"camera_{camera_id}")
        
        # Verificar si hay otros clientes en el room
        room_clients = sio.manager.get_participants(sio.namespace, f"camera_{camera_id}")
        if len(room_clients) == 0:
            # No hay más clientes, detener stream
            await camera_manager.stop_stream(camera_id)
        
        await sio.emit('left_stream', {
            'camera_id': camera_id,
            'message': f'Saliste del stream de la cámara {camera_id}'
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Error al salir del stream: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def get_camera_list(sid, data):
    """Obtener lista de cámaras disponibles"""
    try:
        cameras = await camera_manager.get_cameras()
        await sio.emit('camera_list', {'cameras': cameras}, room=sid)
    except Exception as e:
        logger.error(f"Error al obtener lista de cámaras: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

# Endpoints básicos
@app.get("/api")
async def api_root():
    """Endpoint raíz de la API"""
    return {
        "message": "RTSP to WebRTC API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cameras_active": len(camera_manager.active_streams),
        "webrtc_connections": len(webrtc_service.active_connections)
    }

# Crear aplicación ASGI con Socket.IO
socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    uvicorn.run(
        "src.presentation.api.main:socket_app",
        host="0.0.0.0",
        port=8990,
        reload=True,
        log_level="info"
    )