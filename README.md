# 🎥 RTSP to WebRTC API

Una API completa desarrollada con **FastAPI** que captura streams RTSP de cámaras de videovigilancia, aplica detección de movimiento usando **OpenCV**, y transmite el video procesado a través de **WebRTC** y **Socket.IO** para mínima latencia.

## ✨ Características

- 📹 **Captura RTSP**: Soporte para múltiples cámaras IP
- 🔍 **Detección de Movimiento**: Usando OpenCV BackgroundSubtractor
- 🎯 **Overlay Visual**: Resaltado de áreas con movimiento detectado
- 🚀 **WebRTC Streaming**: Transmisión de baja latencia
- 🔌 **Socket.IO**: Stream alternativo en tiempo real
- 🎮 **GPU Acceleration**: Soporte para NVIDIA CUDA
- 🌐 **API RESTful**: Endpoints completos para gestión
- 📱 **Cliente Web**: Interfaz de demostración incluida
- 🐳 **Docker Ready**: Configuración completa con Docker Compose

## 🏗️ Arquitectura

```
src/
├── core/                   # Configuración central
│   ├── config.py          # Settings y configuración
│   └── __init__.py
├── infrastructure/         # Servicios de infraestructura
│   └── services/
│       ├── camera_manager.py    # Gestión de cámaras RTSP
│       ├── webrtc_service.py    # Servicio WebRTC
│       └── __init__.py
└── presentation/          # Capa de presentación
    └── api/
        ├── routes/        # Rutas de la API
        │   ├── camera_routes.py
        │   ├── streaming_routes.py
        │   └── __init__.py
        ├── main.py        # Aplicación FastAPI principal
        └── __init__.py
```

## 🚀 Instalación Rápida

### Usando Docker (Recomendado)

```bash
# Clonar el repositorio
git clone <repository-url>
cd rtsp_to_webrtc_cv2

# Construir y ejecutar con Docker Compose
docker-compose up --build
```

### Instalación Manual

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python run.py
```

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` o modifica el existente:

```env
# Aplicación
APP_NAME=RTSP to WebRTC API
APP_VERSION=1.0.0
ENVIRONMENT=development

# Servidor
HOST=0.0.0.0
PORT=8990

# Detección de Movimiento
MOTION_THRESHOLD=25
MOTION_MIN_AREA=500
MOTION_BLUR_SIZE=21

# Video
VIDEO_WIDTH=640
VIDEO_HEIGHT=480
VIDEO_FPS=30

# GPU (NVIDIA)
USE_GPU=true
GPU_DEVICE_ID=0

# Almacenamiento
STORAGE_PATH=./storage
LOGS_PATH=./logs

# Seguridad
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=["*"]

# Socket.IO
SOCKETIO_CORS_ALLOWED_ORIGINS=["*"]
SOCKETIO_ASYNC_MODE=asgi

# WebRTC
WEBRTC_ICE_SERVERS=["stun:stun.l.google.com:19302"]

# Cámaras RTSP (JSON)
RTSP_CAMERAS={
  "camera_1": {
    "name": "Cámara Principal",
    "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
    "enabled": true
  }
}
```

### Configuración de Cámaras

Las cámaras se configuran en el archivo `.env` usando formato JSON:

```json
{
  "camera_1": {
    "name": "Cámara Entrada",
    "url": "rtsp://admin:Sec7442019@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
    "enabled": true
  },
  "camera_2": {
    "name": "Cámara Parking",
    "url": "rtsp://admin:Sec7442019@192.168.1.11:554/cam/realmonitor?channel=1&subtype=1",
    "enabled": true
  }
}
```

## 🎮 Uso

### 1. Iniciar la Aplicación

```bash
python run.py
```

### 2. Acceder a la Interfaz Web

Abre tu navegador en: `http://localhost:8990`

### 3. API Endpoints

#### Gestión de Cámaras

```bash
# Listar cámaras
GET /api/cameras/

# Iniciar stream de cámara
POST /api/cameras/{camera_id}/start

# Detener stream de cámara
POST /api/cameras/{camera_id}/stop

# Estado de cámara
GET /api/cameras/{camera_id}/status
```

#### WebRTC Streaming

```bash
# Crear oferta WebRTC
POST /api/streaming/webrtc/offer
{
  "camera_id": "camera_1"
}

# Enviar respuesta WebRTC
POST /api/streaming/webrtc/answer
{
  "connection_id": "uuid",
  "sdp": "...",
  "type": "answer"
}

# Agregar candidato ICE
POST /api/streaming/webrtc/ice-candidate
{
  "connection_id": "uuid",
  "candidate": {...}
}
```

### 4. Socket.IO Events

```javascript
// Conectar al stream
socket.emit('join_camera_stream', { camera_id: 'camera_1' });

// Recibir frames
socket.on('video_frame', (data) => {
  // data.frame contiene la imagen en base64
  // data.camera_id identifica la cámara
  // data.motion_detected indica si hay movimiento
});

// Desconectar del stream
socket.emit('leave_camera_stream', { camera_id: 'camera_1' });
```

## 🔧 Desarrollo

### Estructura del Proyecto

- **Core**: Configuración y utilidades centrales
- **Infrastructure**: Servicios de captura de video y WebRTC
- **Presentation**: API REST y WebSocket endpoints

### Ejecutar en Modo Desarrollo

```bash
# Con recarga automática
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8990
```

### Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=src
```

## 🐳 Docker

### Dockerfile

El proyecto incluye un Dockerfile optimizado para:
- Soporte NVIDIA GPU
- Dependencias OpenCV
- Configuración de producción

### Docker Compose

```yaml
version: '3.8'
services:
  rtsp-webrtc-api:
    build: .
    ports:
      - "8990:8990"
    environment:
      - USE_GPU=true
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 📱 Cliente Flutter

Para integrar con Flutter, usa el paquete `flutter_webrtc`:

```dart
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

class RTSPWebRTCClient {
  late RTCPeerConnection _peerConnection;
  late IO.Socket _socket;
  
  Future<void> connectToCamera(String cameraId) async {
    // Configurar WebRTC
    _peerConnection = await createPeerConnection({
      'iceServers': [
        {'urls': 'stun:stun.l.google.com:19302'}
      ]
    });
    
    // Configurar Socket.IO
    _socket = IO.io('http://your-api-url:8990');
    _socket.emit('join_camera_stream', {'camera_id': cameraId});
  }
}
```

## 🔍 Detección de Movimiento

El sistema utiliza OpenCV para detectar movimiento:

1. **Background Subtraction**: Usando `cv2.createBackgroundSubtractorMOG2()`
2. **Filtrado**: Aplicación de filtros morfológicos
3. **Contornos**: Detección de áreas de movimiento
4. **Overlay**: Resaltado visual de las áreas detectadas

### Parámetros Configurables

- `MOTION_THRESHOLD`: Sensibilidad de detección
- `MOTION_MIN_AREA`: Área mínima para considerar movimiento
- `MOTION_BLUR_SIZE`: Tamaño del filtro de desenfoque

## 🚨 Troubleshooting

### Problemas Comunes

1. **Error de conexión RTSP**
   ```
   Verificar URL, credenciales y conectividad de red
   ```

2. **GPU no detectada**
   ```bash
   # Verificar CUDA
   nvidia-smi
   
   # Instalar drivers NVIDIA
   # Configurar USE_GPU=false para usar CPU
   ```

3. **WebRTC no funciona**
   ```
   Verificar configuración de ICE servers
   Comprobar firewall y NAT
   ```

## 📊 Monitoreo

### Logs

Los logs se guardan en:
- Consola: Tiempo real con colores
- Archivo: `./logs/app.log` (rotación automática)

### Métricas

Endpoints de monitoreo:
- `/health`: Estado de la aplicación
- `/api/streaming/webrtc/stats`: Estadísticas WebRTC
- `/api/cameras/{id}/status`: Estado de cámaras

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [OpenCV](https://opencv.org/) - Biblioteca de visión por computadora
- [aiortc](https://github.com/aiortc/aiortc) - WebRTC para Python
- [Socket.IO](https://socket.io/) - Comunicación en tiempo real

---

**Desarrollado con ❤️ para videovigilancia inteligente**