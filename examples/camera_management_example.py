"""
Ejemplo de uso de la API de gestión de cámaras RTSP
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any


class CameraAPIClient:
    """Cliente para la API de gestión de cámaras"""
    
    def __init__(self, base_url: str = "http://localhost:8990"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v2/cameras"
        
    async def create_camera(self, camera_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear una nueva cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=camera_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Error creando cámara: {error}")
    
    async def list_cameras(self) -> Dict[str, Any]:
        """Listar todas las cámaras"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Error listando cámaras: {error}")
    
    async def get_camera(self, camera_id: str) -> Dict[str, Any]:
        """Obtener información de una cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/{camera_id}") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    error = await response.text()
                    raise Exception(f"Error obteniendo cámara: {error}")
    
    async def update_camera(self, camera_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar una cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.api_url}/{camera_id}", json=updates) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    error = await response.text()
                    raise Exception(f"Error actualizando cámara: {error}")
    
    async def delete_camera(self, camera_id: str) -> bool:
        """Eliminar una cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.api_url}/{camera_id}") as response:
                if response.status == 204:
                    return True
                elif response.status == 404:
                    return False
                else:
                    error = await response.text()
                    raise Exception(f"Error eliminando cámara: {error}")
    
    async def test_camera(self, camera_id: str) -> Dict[str, Any]:
        """Probar conexión de una cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/{camera_id}/test") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Error probando cámara: {error}")
    
    async def get_camera_status(self, camera_id: str) -> Dict[str, Any]:
        """Obtener estado de una cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/{camera_id}/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Error obteniendo estado: {error}")
    
    async def enable_camera(self, camera_id: str) -> Dict[str, Any]:
        """Habilitar una cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/{camera_id}/enable") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Error habilitando cámara: {error}")
    
    async def disable_camera(self, camera_id: str) -> Dict[str, Any]:
        """Deshabilitar una cámara"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/{camera_id}/disable") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Error deshabilitando cámara: {error}")
    
    async def create_cameras_bulk(self, cameras_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crear múltiples cámaras en lote"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/bulk", json=cameras_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Error creando cámaras en lote: {error}")


async def example_usage():
    """Ejemplo de uso de la API de cámaras"""
    
    client = CameraAPIClient()
    
    print("🎥 Ejemplo de gestión de cámaras RTSP")
    print("=" * 50)
    
    try:
        # 1. Crear cámaras de ejemplo
        print("\n1. Creando cámaras de ejemplo...")
        
        cameras_to_create = [
            {
                "id": "camera_office",
                "name": "Cámara Oficina",
                "url": "rtsp://admin:password@192.168.1.10:554/cam/realmonitor?channel=1&subtype=1",
                "type": "rtsp",
                "location": "Oficina Principal",
                "description": "Cámara de seguridad de la oficina",
                "resolution": "1920x1080",
                "fps": 30,
                "enabled": True,
                "metadata": {
                    "zone": "interior",
                    "priority": "high"
                }
            },
            {
                "id": "camera_entrance",
                "name": "Cámara Entrada",
                "url": "rtsp://admin:password@192.168.1.11:554/cam/realmonitor?channel=1&subtype=1",
                "type": "rtsp",
                "location": "Entrada Principal",
                "description": "Cámara de la entrada del edificio",
                "resolution": "1920x1080",
                "fps": 25,
                "enabled": True,
                "metadata": {
                    "zone": "exterior",
                    "priority": "high"
                }
            },
            {
                "id": "camera_parking",
                "name": "Cámara Estacionamiento",
                "url": "rtsp://admin:password@192.168.1.12:554/cam/realmonitor?channel=1&subtype=1",
                "type": "rtsp",
                "location": "Estacionamiento",
                "description": "Cámara del área de estacionamiento",
                "resolution": "1280x720",
                "fps": 20,
                "enabled": False,
                "metadata": {
                    "zone": "exterior",
                    "priority": "medium"
                }
            }
        ]
        
        # Crear cámaras individualmente
        created_cameras = []
        for camera_data in cameras_to_create:
            try:
                camera = await client.create_camera(camera_data)
                created_cameras.append(camera)
                print(f"✅ Cámara creada: {camera['name']} ({camera['id']})")
            except Exception as e:
                print(f"❌ Error creando cámara {camera_data['id']}: {e}")
        
        # 2. Listar todas las cámaras
        print("\n2. Listando todas las cámaras...")
        cameras_list = await client.list_cameras()
        print(f"📋 Total de cámaras: {cameras_list['total']}")
        print(f"🟢 Activas: {cameras_list['active']}")
        print(f"🔴 Inactivas: {cameras_list['inactive']}")
        
        for camera in cameras_list['cameras']:
            status_emoji = "🟢" if camera['status'] == 'active' else "🔴"
            enabled_emoji = "✅" if camera['enabled'] else "❌"
            print(f"  {status_emoji} {camera['name']} ({camera['id']}) - {enabled_emoji}")
        
        # 3. Obtener información detallada de una cámara
        print("\n3. Obteniendo información detallada...")
        if created_cameras:
            camera_id = created_cameras[0]['id']
            camera_detail = await client.get_camera(camera_id)
            if camera_detail:
                print(f"📹 Cámara: {camera_detail['name']}")
                print(f"   URL: {camera_detail['url']}")
                print(f"   Estado: {camera_detail['status']}")
                print(f"   Ubicación: {camera_detail['location']}")
                print(f"   Resolución: {camera_detail['resolution']}")
                print(f"   FPS: {camera_detail['fps']}")
        
        # 4. Probar conexión de cámaras
        print("\n4. Probando conexiones...")
        for camera in created_cameras:
            try:
                test_result = await client.test_camera(camera['id'])
                status = "✅ Conectada" if test_result['connection_test'] == 'success' else "❌ Error"
                print(f"  {camera['name']}: {status}")
            except Exception as e:
                print(f"  {camera['name']}: ❌ Error - {e}")
        
        # 5. Actualizar una cámara
        print("\n5. Actualizando configuración...")
        if created_cameras:
            camera_id = created_cameras[0]['id']
            updates = {
                "description": "Cámara de oficina - Actualizada",
                "fps": 25,
                "metadata": {
                    "zone": "interior",
                    "priority": "high",
                    "updated": True
                }
            }
            
            updated_camera = await client.update_camera(camera_id, updates)
            if updated_camera:
                print(f"✅ Cámara actualizada: {updated_camera['name']}")
                print(f"   Nueva descripción: {updated_camera['description']}")
                print(f"   Nuevo FPS: {updated_camera['fps']}")
        
        # 6. Habilitar/Deshabilitar cámaras
        print("\n6. Gestionando estado de cámaras...")
        if len(created_cameras) > 1:
            # Deshabilitar una cámara
            camera_id = created_cameras[1]['id']
            disabled_camera = await client.disable_camera(camera_id)
            print(f"❌ Cámara deshabilitada: {disabled_camera['name']}")
            
            # Habilitarla de nuevo
            enabled_camera = await client.enable_camera(camera_id)
            print(f"✅ Cámara habilitada: {enabled_camera['name']}")
        
        # 7. Obtener estado detallado
        print("\n7. Estado detallado de cámaras...")
        for camera in created_cameras:
            try:
                status = await client.get_camera_status(camera['id'])
                print(f"📊 {status['name']}:")
                print(f"   Estado: {status['status']}")
                print(f"   Habilitada: {status['enabled']}")
                print(f"   Sesiones activas: {status['active_sessions']}")
                print(f"   Última actualización: {status['last_updated']}")
            except Exception as e:
                print(f"❌ Error obteniendo estado de {camera['name']}: {e}")
        
        # 8. Crear cámaras en lote
        print("\n8. Creando cámaras en lote...")
        bulk_cameras = [
            {
                "id": "camera_warehouse_1",
                "name": "Cámara Almacén 1",
                "url": "rtsp://admin:password@192.168.1.20:554/cam/realmonitor?channel=1&subtype=1",
                "type": "rtsp",
                "location": "Almacén - Zona A",
                "enabled": True
            },
            {
                "id": "camera_warehouse_2",
                "name": "Cámara Almacén 2",
                "url": "rtsp://admin:password@192.168.1.21:554/cam/realmonitor?channel=1&subtype=1",
                "type": "rtsp",
                "location": "Almacén - Zona B",
                "enabled": True
            }
        ]
        
        try:
            bulk_result = await client.create_cameras_bulk(bulk_cameras)
            print(f"✅ Cámaras creadas en lote: {len(bulk_result)}")
            for camera in bulk_result:
                print(f"   - {camera['name']} ({camera['id']})")
        except Exception as e:
            print(f"❌ Error en creación en lote: {e}")
        
        # 9. Lista final de cámaras
        print("\n9. Lista final de cámaras...")
        final_list = await client.list_cameras()
        print(f"📋 Total final: {final_list['total']} cámaras")
        
        # 10. Limpiar - eliminar cámaras de ejemplo
        print("\n10. Limpiando cámaras de ejemplo...")
        all_cameras = final_list['cameras']
        example_cameras = [c for c in all_cameras if c['id'].startswith(('camera_office', 'camera_entrance', 'camera_parking', 'camera_warehouse'))]
        
        for camera in example_cameras:
            try:
                success = await client.delete_camera(camera['id'])
                if success:
                    print(f"🗑️ Cámara eliminada: {camera['name']}")
                else:
                    print(f"❌ No se pudo eliminar: {camera['name']}")
            except Exception as e:
                print(f"❌ Error eliminando {camera['name']}: {e}")
        
        print("\n✅ Ejemplo completado exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en el ejemplo: {e}")


async def frontend_connection_example():
    """Ejemplo de cómo conectarse desde el frontend por ID de cámara"""
    
    print("\n🌐 Ejemplo de conexión desde el frontend")
    print("=" * 50)
    
    # Código JavaScript que se usaría en el frontend
    frontend_code = """
    // Ejemplo de código JavaScript para el frontend
    
    class RTSPCameraClient {
        constructor(serverUrl = 'http://localhost:8990') {
            this.serverUrl = serverUrl;
            this.socket = null;
            this.cameras = new Map();
        }
        
        // Conectar al servidor Socket.IO
        async connect() {
            this.socket = io(this.serverUrl);
            
            this.socket.on('connect', () => {
                console.log('Conectado al servidor RTSP');
            });
            
            this.socket.on('camera_list', (data) => {
                this.updateCameraList(data.cameras);
            });
            
            this.socket.on('frame_data', (data) => {
                this.displayFrame(data.camera_id, data.frame, data.motion_detected);
            });
        }
        
        // Obtener lista de cámaras disponibles
        async getCameras() {
            const response = await fetch(`${this.serverUrl}/api/v2/cameras`);
            const data = await response.json();
            return data.cameras;
        }
        
        // Conectar a una cámara específica por ID
        async connectToCamera(cameraId) {
            // Verificar que la cámara existe
            const camera = await this.getCameraById(cameraId);
            if (!camera) {
                throw new Error(`Cámara ${cameraId} no encontrada`);
            }
            
            if (!camera.enabled) {
                throw new Error(`Cámara ${cameraId} está deshabilitada`);
            }
            
            // Unirse al stream de la cámara
            this.socket.emit('join_camera_stream', { camera_id: cameraId });
            
            return new Promise((resolve, reject) => {
                this.socket.once('joined_stream', (data) => {
                    if (data.camera_id === cameraId) {
                        console.log(`Conectado a cámara: ${cameraId}`);
                        resolve(data);
                    }
                });
                
                this.socket.once('error', (error) => {
                    reject(new Error(error.message));
                });
            });
        }
        
        // Desconectar de una cámara
        async disconnectFromCamera(cameraId) {
            this.socket.emit('leave_camera_stream', { camera_id: cameraId });
        }
        
        // Obtener información de una cámara por ID
        async getCameraById(cameraId) {
            const response = await fetch(`${this.serverUrl}/api/v2/cameras/${cameraId}`);
            if (response.status === 404) {
                return null;
            }
            return await response.json();
        }
        
        // Mostrar frame en el elemento de video
        displayFrame(cameraId, frameData, motionDetected) {
            const videoElement = document.getElementById(`camera-${cameraId}`);
            if (videoElement) {
                videoElement.src = `data:image/jpeg;base64,${frameData}`;
                
                // Indicar detección de movimiento
                const container = videoElement.parentElement;
                if (motionDetected) {
                    container.classList.add('motion-detected');
                } else {
                    container.classList.remove('motion-detected');
                }
            }
        }
        
        // Actualizar lista de cámaras en la UI
        updateCameraList(cameras) {
            const cameraList = document.getElementById('camera-list');
            cameraList.innerHTML = '';
            
            cameras.forEach(camera => {
                const cameraElement = document.createElement('div');
                cameraElement.className = 'camera-item';
                cameraElement.innerHTML = `
                    <h3>${camera.name}</h3>
                    <p>ID: ${camera.id}</p>
                    <p>Estado: ${camera.status}</p>
                    <p>Ubicación: ${camera.location || 'No especificada'}</p>
                    <button onclick="connectToCamera('${camera.id}')">
                        Conectar
                    </button>
                    <div class="video-container">
                        <img id="camera-${camera.id}" alt="${camera.name}" />
                    </div>
                `;
                cameraList.appendChild(cameraElement);
            });
        }
    }
    
    // Uso del cliente
    const client = new RTSPCameraClient();
    
    // Inicializar
    client.connect();
    
    // Función global para conectar a cámara
    async function connectToCamera(cameraId) {
        try {
            await client.connectToCamera(cameraId);
            console.log(`Conectado a cámara: ${cameraId}`);
        } catch (error) {
            console.error(`Error conectando a cámara ${cameraId}:`, error);
            alert(`Error: ${error.message}`);
        }
    }
    
    // Cargar lista de cámaras al iniciar
    window.addEventListener('load', async () => {
        try {
            const cameras = await client.getCameras();
            client.updateCameraList(cameras);
        } catch (error) {
            console.error('Error cargando cámaras:', error);
        }
    });
    """
    
    print("📝 Código JavaScript para el frontend:")
    print(frontend_code)
    
    # Ejemplo de HTML
    html_example = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RTSP Camera Viewer</title>
        <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
        <style>
            .camera-item {
                border: 1px solid #ccc;
                margin: 10px;
                padding: 10px;
                border-radius: 5px;
            }
            .video-container {
                margin-top: 10px;
            }
            .video-container img {
                max-width: 100%;
                height: auto;
            }
            .motion-detected {
                border: 3px solid red;
                animation: blink 1s infinite;
            }
            @keyframes blink {
                0%, 50% { border-color: red; }
                51%, 100% { border-color: transparent; }
            }
        </style>
    </head>
    <body>
        <h1>RTSP Camera Viewer</h1>
        <div id="camera-list"></div>
        
        <script>
            // Aquí iría el código JavaScript del cliente
        </script>
    </body>
    </html>
    """
    
    print("\n📄 Ejemplo de HTML:")
    print(html_example)


if __name__ == "__main__":
    print("🚀 Iniciando ejemplos de gestión de cámaras RTSP")
    
    # Ejecutar ejemplo de API
    asyncio.run(example_usage())
    
    # Mostrar ejemplo de frontend
    asyncio.run(frontend_connection_example())