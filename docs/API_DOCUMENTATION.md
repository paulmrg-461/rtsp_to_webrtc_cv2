# 📹 API de Gestión de Cámaras RTSP

## Descripción General

Esta API permite gestionar múltiples cámaras RTSP, configurarlas, monitorearlas y conectarse a sus streams desde el frontend usando identificadores únicos.

## URL Base

```
http://localhost:8990/api/v2
```

## Autenticación

Actualmente no se requiere autenticación. En producción se recomienda implementar autenticación JWT o similar.

---

## 📋 Endpoints de Cámaras

### 1. Crear Cámara

**POST** `/cameras`

Crea una nueva cámara RTSP en el sistema.

#### Request Body

```json
{
  "id": "camera_office",
  "name": "Cámara Oficina",
  "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
  "type": "rtsp",
  "location": "Oficina Principal",
  "description": "Cámara de seguridad de la oficina",
  "resolution": "1920x1080",
  "fps": 30,
  "enabled": true,
  "metadata": {
    "zone": "interior",
    "priority": "high"
  }
}
```

#### Response (201 Created)

```json
{
  "id": "camera_office",
  "name": "Cámara Oficina",
  "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
  "type": "rtsp",
  "status": "inactive",
  "location": "Oficina Principal",
  "description": "Cámara de seguridad de la oficina",
  "resolution": "1920x1080",
  "fps": 30,
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "zone": "interior",
    "priority": "high"
  }
}
```

#### Errores

- **400 Bad Request**: Datos inválidos o cámara ya existe
- **500 Internal Server Error**: Error interno del servidor

---

### 2. Listar Cámaras

**GET** `/cameras`

Obtiene la lista de todas las cámaras registradas.

#### Query Parameters

- `enabled` (opcional): `true` o `false` para filtrar por estado
- `status` (opcional): `active`, `inactive`, `error` para filtrar por estado
- `limit` (opcional): Número máximo de resultados (default: 100)
- `offset` (opcional): Número de resultados a omitir (default: 0)

#### Response (200 OK)

```json
{
  "cameras": [
    {
      "id": "camera_office",
      "name": "Cámara Oficina",
      "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
      "type": "rtsp",
      "status": "active",
      "location": "Oficina Principal",
      "description": "Cámara de seguridad de la oficina",
      "resolution": "1920x1080",
      "fps": 30,
      "enabled": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "metadata": {
        "zone": "interior",
        "priority": "high"
      }
    }
  ],
  "total": 1,
  "active": 1,
  "inactive": 0,
  "enabled": 1,
  "disabled": 0
}
```

---

### 3. Obtener Cámara por ID

**GET** `/cameras/{camera_id}`

Obtiene información detallada de una cámara específica.

#### Path Parameters

- `camera_id`: ID único de la cámara

#### Response (200 OK)

```json
{
  "id": "camera_office",
  "name": "Cámara Oficina",
  "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
  "type": "rtsp",
  "status": "active",
  "location": "Oficina Principal",
  "description": "Cámara de seguridad de la oficina",
  "resolution": "1920x1080",
  "fps": 30,
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "zone": "interior",
    "priority": "high"
  }
}
```

#### Errores

- **404 Not Found**: Cámara no encontrada

---

### 4. Actualizar Cámara

**PUT** `/cameras/{camera_id}`

Actualiza la configuración de una cámara existente.

#### Path Parameters

- `camera_id`: ID único de la cámara

#### Request Body

```json
{
  "name": "Cámara Oficina - Actualizada",
  "description": "Cámara de seguridad de la oficina principal",
  "fps": 25,
  "metadata": {
    "zone": "interior",
    "priority": "high",
    "updated": true
  }
}
```

#### Response (200 OK)

```json
{
  "id": "camera_office",
  "name": "Cámara Oficina - Actualizada",
  "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
  "type": "rtsp",
  "status": "active",
  "location": "Oficina Principal",
  "description": "Cámara de seguridad de la oficina principal",
  "resolution": "1920x1080",
  "fps": 25,
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "metadata": {
    "zone": "interior",
    "priority": "high",
    "updated": true
  }
}
```

#### Errores

- **404 Not Found**: Cámara no encontrada
- **400 Bad Request**: Datos inválidos

---

### 5. Eliminar Cámara

**DELETE** `/cameras/{camera_id}`

Elimina una cámara del sistema.

#### Path Parameters

- `camera_id`: ID único de la cámara

#### Response (204 No Content)

Sin contenido en el cuerpo de la respuesta.

#### Errores

- **404 Not Found**: Cámara no encontrada

---

### 6. Habilitar Cámara

**POST** `/cameras/{camera_id}/enable`

Habilita una cámara para que pueda ser utilizada.

#### Path Parameters

- `camera_id`: ID único de la cámara

#### Response (200 OK)

```json
{
  "id": "camera_office",
  "name": "Cámara Oficina",
  "enabled": true,
  "status": "active",
  "message": "Cámara habilitada exitosamente"
}
```

---

### 7. Deshabilitar Cámara

**POST** `/cameras/{camera_id}/disable`

Deshabilita una cámara para que no pueda ser utilizada.

#### Path Parameters

- `camera_id`: ID único de la cámara

#### Response (200 OK)

```json
{
  "id": "camera_office",
  "name": "Cámara Oficina",
  "enabled": false,
  "status": "inactive",
  "message": "Cámara deshabilitada exitosamente"
}
```

---

### 8. Probar Conexión

**POST** `/cameras/{camera_id}/test`

Prueba la conexión a una cámara RTSP.

#### Path Parameters

- `camera_id`: ID único de la cámara

#### Response (200 OK)

```json
{
  "camera_id": "camera_office",
  "camera_name": "Cámara Oficina",
  "connection_test": "success",
  "response_time_ms": 1250,
  "message": "Conexión exitosa",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

#### Response (200 OK - Error de conexión)

```json
{
  "camera_id": "camera_office",
  "camera_name": "Cámara Oficina",
  "connection_test": "failed",
  "error": "Connection timeout",
  "message": "No se pudo conectar a la cámara",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

### 9. Obtener Estado de Cámara

**GET** `/cameras/{camera_id}/status`

Obtiene el estado actual y estadísticas de una cámara.

#### Path Parameters

- `camera_id`: ID único de la cámara

#### Response (200 OK)

```json
{
  "camera_id": "camera_office",
  "name": "Cámara Oficina",
  "status": "active",
  "enabled": true,
  "active_sessions": 2,
  "last_frame_time": "2024-01-15T12:00:00Z",
  "uptime_seconds": 3600,
  "frames_processed": 108000,
  "motion_events": 15,
  "last_updated": "2024-01-15T12:00:00Z"
}
```

---

### 10. Crear Cámaras en Lote

**POST** `/cameras/bulk`

Crea múltiples cámaras en una sola operación.

#### Request Body

```json
[
  {
    "id": "camera_warehouse_1",
    "name": "Cámara Almacén 1",
    "url": "rtsp://admin:password@192.168.1.20:554/cam/realmonitor?channel=1&subtype=1",
    "type": "rtsp",
    "location": "Almacén - Zona A",
    "enabled": true
  },
  {
    "id": "camera_warehouse_2",
    "name": "Cámara Almacén 2",
    "url": "rtsp://admin:password@192.168.1.21:554/cam/realmonitor?channel=1&subtype=1",
    "type": "rtsp",
    "location": "Almacén - Zona B",
    "enabled": true
  }
]
```

#### Response (200 OK)

```json
[
  {
    "id": "camera_warehouse_1",
    "name": "Cámara Almacén 1",
    "status": "created",
    "message": "Cámara creada exitosamente"
  },
  {
    "id": "camera_warehouse_2",
    "name": "Cámara Almacén 2",
    "status": "created",
    "message": "Cámara creada exitosamente"
  }
]
```

---

## 🔌 Conexión WebSocket/Socket.IO

Para recibir streams de video en tiempo real, utiliza Socket.IO:

### Eventos del Cliente

#### `join_camera_stream`

Unirse al stream de una cámara específica.

```javascript
socket.emit('join_camera_stream', { camera_id: 'camera_office' });
```

#### `leave_camera_stream`

Salir del stream de una cámara.

```javascript
socket.emit('leave_camera_stream', { camera_id: 'camera_office' });
```

### Eventos del Servidor

#### `joined_stream`

Confirmación de que se unió al stream.

```javascript
socket.on('joined_stream', (data) => {
  console.log(`Conectado a cámara: ${data.camera_id}`);
});
```

#### `left_stream`

Confirmación de que salió del stream.

```javascript
socket.on('left_stream', (data) => {
  console.log(`Desconectado de cámara: ${data.camera_id}`);
});
```

#### `frame_data`

Recibe frames de video en tiempo real.

```javascript
socket.on('frame_data', (data) => {
  const { camera_id, frame, motion_detected, timestamp } = data;
  
  // Mostrar frame en elemento de imagen
  const imgElement = document.getElementById(`camera-${camera_id}`);
  imgElement.src = `data:image/jpeg;base64,${frame}`;
  
  // Manejar detección de movimiento
  if (motion_detected) {
    console.log(`Movimiento detectado en cámara: ${camera_id}`);
  }
});
```

#### `camera_list`

Lista actualizada de cámaras disponibles.

```javascript
socket.on('camera_list', (data) => {
  console.log('Cámaras disponibles:', data.cameras);
});
```

---

## 📝 Modelos de Datos

### CameraConfig

```typescript
interface CameraConfig {
  id: string;                    // ID único de la cámara
  name: string;                  // Nombre descriptivo
  url: string;                   // URL RTSP
  type: "rtsp" | "http" | "file"; // Tipo de fuente
  status: "active" | "inactive" | "error"; // Estado actual
  location?: string;             // Ubicación física
  description?: string;          // Descripción detallada
  resolution?: string;           // Resolución (ej: "1920x1080")
  fps?: number;                  // Frames por segundo
  enabled: boolean;              // Si está habilitada
  created_at: string;            // Fecha de creación (ISO 8601)
  updated_at: string;            // Fecha de actualización (ISO 8601)
  metadata?: Record<string, any>; // Metadatos adicionales
}
```

### CameraCreateRequest

```typescript
interface CameraCreateRequest {
  id: string;
  name: string;
  url: string;
  type?: "rtsp" | "http" | "file";
  location?: string;
  description?: string;
  resolution?: string;
  fps?: number;
  enabled?: boolean;
  metadata?: Record<string, any>;
}
```

### CameraUpdateRequest

```typescript
interface CameraUpdateRequest {
  name?: string;
  url?: string;
  location?: string;
  description?: string;
  resolution?: string;
  fps?: number;
  enabled?: boolean;
  metadata?: Record<string, any>;
}
```

---

## 🚀 Ejemplos de Uso

### 1. Configurar Múltiples Cámaras

```python
import asyncio
import aiohttp

async def setup_cameras():
    cameras = [
        {
            "id": "camera_entrance",
            "name": "Cámara Entrada",
            "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
            "location": "Entrada Principal",
            "enabled": True
        },
        {
            "id": "camera_office",
            "name": "Cámara Oficina",
            "url": "rtsp://admin:password@192.168.1.11:554/cam/realmonitor?channel=1&subtype=1",
            "location": "Oficina",
            "enabled": True
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for camera in cameras:
            async with session.post('http://localhost:8990/api/v2/cameras', json=camera) as response:
                if response.status == 201:
                    result = await response.json()
                    print(f"✅ Cámara creada: {result['name']}")
                else:
                    error = await response.text()
                    print(f"❌ Error: {error}")

# Ejecutar
asyncio.run(setup_cameras())
```

### 2. Conectar desde Frontend

```javascript
// Conectar al servidor
const socket = io('http://localhost:8990');

// Obtener lista de cámaras
async function loadCameras() {
    const response = await fetch('http://localhost:8990/api/v2/cameras');
    const data = await response.json();
    
    data.cameras.forEach(camera => {
        console.log(`Cámara disponible: ${camera.name} (${camera.id})`);
    });
    
    return data.cameras;
}

// Conectar a una cámara específica
function connectToCamera(cameraId) {
    socket.emit('join_camera_stream', { camera_id: cameraId });
}

// Recibir frames
socket.on('frame_data', (data) => {
    const imgElement = document.getElementById(`camera-${data.camera_id}`);
    imgElement.src = `data:image/jpeg;base64,${data.frame}`;
    
    if (data.motion_detected) {
        console.log(`🚨 Movimiento detectado en ${data.camera_id}`);
    }
});

// Inicializar
loadCameras().then(cameras => {
    // Conectar a la primera cámara habilitada
    const enabledCamera = cameras.find(c => c.enabled);
    if (enabledCamera) {
        connectToCamera(enabledCamera.id);
    }
});
```

### 3. Monitoreo de Estado

```python
import asyncio
import aiohttp

async def monitor_cameras():
    async with aiohttp.ClientSession() as session:
        # Obtener lista de cámaras
        async with session.get('http://localhost:8990/api/v2/cameras') as response:
            data = await response.json()
            cameras = data['cameras']
        
        # Probar conexión de cada cámara
        for camera in cameras:
            async with session.post(f'http://localhost:8990/api/v2/cameras/{camera["id"]}/test') as response:
                result = await response.json()
                
                if result['connection_test'] == 'success':
                    print(f"✅ {camera['name']}: Conectada ({result['response_time_ms']}ms)")
                else:
                    print(f"❌ {camera['name']}: Error - {result.get('error', 'Desconocido')}")

# Ejecutar cada 30 segundos
async def continuous_monitoring():
    while True:
        await monitor_cameras()
        await asyncio.sleep(30)

asyncio.run(continuous_monitoring())
```

---

## 🔧 Configuración

### Variables de Entorno

```bash
# Puerto del servidor
PORT=8990

# Host del servidor
HOST=0.0.0.0

# Configuración de Socket.IO
SOCKETIO_ASYNC_MODE=asgi

# Configuración de cámaras
DEFAULT_CAMERA_FPS=25
DEFAULT_CAMERA_RESOLUTION=1920x1080
MAX_CAMERAS=50

# Configuración de detección de movimiento
MOTION_DETECTION_ENABLED=true
MOTION_THRESHOLD=30
```

### Configuración Docker

```yaml
# docker-compose.yml
version: '3.8'
services:
  rtsp-server:
    build: .
    ports:
      - "8990:8990"
    environment:
      - PORT=8990
      - HOST=0.0.0.0
      - SOCKETIO_ASYNC_MODE=asgi
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
```

---

## 🐛 Códigos de Error

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 201 | Recurso creado exitosamente |
| 204 | Operación exitosa sin contenido |
| 400 | Solicitud inválida |
| 404 | Recurso no encontrado |
| 409 | Conflicto (recurso ya existe) |
| 500 | Error interno del servidor |

### Formato de Error

```json
{
  "error": "Camera not found",
  "message": "La cámara con ID 'camera_invalid' no fue encontrada",
  "code": "CAMERA_NOT_FOUND",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

## 📊 Límites y Consideraciones

- **Máximo de cámaras simultáneas**: 50 (configurable)
- **Máximo de conexiones por cámara**: 10
- **Timeout de conexión RTSP**: 30 segundos
- **Tamaño máximo de frame**: 2MB
- **Rate limiting**: 100 requests/minuto por IP

---

## 🔄 Versionado

Esta documentación corresponde a la **API v2**. Para mantener compatibilidad:

- **v1**: `/api/v1/` (deprecated)
- **v2**: `/api/v2/` (actual)

---

## 📞 Soporte

Para reportar problemas o solicitar nuevas funcionalidades:

1. Revisar los logs del servidor
2. Verificar la conectividad de red
3. Comprobar las credenciales RTSP
4. Consultar esta documentación

---

*Última actualización: 2024-01-15*