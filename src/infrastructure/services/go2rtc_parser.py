"""
Parser para extraer configuraciones de cámaras desde go2rtc.yaml
"""
import yaml
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Go2RTCCamera:
    """Representación de una cámara extraída de go2rtc.yaml"""
    stream_id: str
    rtsp_url: str
    ip_address: str
    username: str
    password: str
    port: int
    channel: int
    subtype: int
    bitrate: Optional[str] = None
    fps: Optional[int] = None
    is_hd: bool = False
    description: Optional[str] = None
    camera_type: Optional[str] = None

class Go2RTCParser:
    """Parser para archivos de configuración go2rtc.yaml"""
    
    def __init__(self, yaml_file_path: str):
        self.yaml_file_path = Path(yaml_file_path)
        self.cameras: List[Go2RTCCamera] = []
        
    def parse_yaml(self) -> Dict:
        """Parsea el archivo YAML y retorna el contenido"""
        try:
            with open(self.yaml_file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Error al parsear {self.yaml_file_path}: {e}")
    
    def extract_rtsp_info(self, rtsp_url: str) -> Tuple[str, str, str, int, int, int, Optional[str], Optional[int]]:
        """
        Extrae información de una URL RTSP
        Retorna: (ip, username, password, port, channel, subtype, bitrate, fps)
        """
        # Patrones para diferentes tipos de URLs RTSP
        patterns = [
            # Patrón estándar: rtsp://username:password@ip:port/path?params#options
            r'rtsp://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?#]+)(?:\?([^#]+))?(?:#(.+))?',
            # Patrón sin credenciales: rtsp://ip:port/path
            r'rtsp://([^:/]+):?(\d+)?/([^?#]+)(?:\?([^#]+))?(?:#(.+))?'
        ]
        
        ip_address = ""
        username = ""
        password = ""
        port = 554  # Puerto por defecto RTSP
        channel = 1
        subtype = 1
        bitrate = None
        fps = None
        
        for pattern in patterns:
            match = re.match(pattern, rtsp_url)
            if match:
                if len(match.groups()) >= 7:  # Patrón con credenciales
                    username, password, ip_address = match.groups()[:3]
                    port_str = match.groups()[3]
                    path = match.groups()[4]
                    query = match.groups()[5]
                    options = match.groups()[6]
                else:  # Patrón sin credenciales
                    ip_address = match.groups()[0]
                    port_str = match.groups()[1]
                    path = match.groups()[2]
                    query = match.groups()[3] if len(match.groups()) > 3 else None
                    options = match.groups()[4] if len(match.groups()) > 4 else None
                
                # Extraer puerto
                if port_str:
                    port = int(port_str)
                
                # Extraer canal del path o query
                if 'channel=' in (query or ''):
                    channel_match = re.search(r'channel=(\d+)', query)
                    if channel_match:
                        channel = int(channel_match.group(1))
                
                # Extraer subtype del path o query
                if 'subtype=' in (query or ''):
                    subtype_match = re.search(r'subtype=(\d+)', query)
                    if subtype_match:
                        subtype = int(subtype_match.group(1))
                
                # Extraer bitrate de las opciones
                if options and 'bitrate=' in options:
                    bitrate_match = re.search(r'bitrate=([^&]+)', options)
                    if bitrate_match:
                        bitrate = bitrate_match.group(1)
                
                # Extraer fps de las opciones
                if options and 'fps=' in options:
                    fps_match = re.search(r'fps=(\d+)', options)
                    if fps_match:
                        fps = int(fps_match.group(1))
                
                break
        
        return ip_address, username, password, port, channel, subtype, bitrate, fps
    
    def detect_camera_type(self, rtsp_url: str, ip_address: str) -> str:
        """Detecta el tipo de cámara basado en la URL RTSP y otros indicadores"""
        url_lower = rtsp_url.lower()
        
        # Detectar por fabricante en la URL
        if 'dahua' in url_lower or 'dh' in url_lower:
            return "DAHUA"
        elif 'hikvision' in url_lower or 'hik' in url_lower:
            return "HIKVISION"
        elif 'axis' in url_lower:
            return "AXIS"
        elif 'onvif' in url_lower:
            return "ONVIF"
        
        # Detectar por patrones de URL
        if '/cam/realmonitor' in url_lower:
            return "DAHUA"
        elif '/streaming/channels/' in url_lower:
            return "HIKVISION"
        elif '/axis-media/media.amp' in url_lower:
            return "AXIS"
        
        # Por defecto, cámara IP genérica
        return "IP_CAMERA"
    
    def parse_cameras(self) -> List[Go2RTCCamera]:
        """Extrae todas las cámaras del archivo YAML"""
        config = self.parse_yaml()
        streams = config.get('streams', {})
        
        cameras = []
        
        for stream_id, stream_urls in streams.items():
            if isinstance(stream_urls, list) and stream_urls:
                rtsp_url = stream_urls[0]  # Tomar la primera URL
                
                # Extraer información de la URL RTSP
                ip, username, password, port, channel, subtype, bitrate, fps = self.extract_rtsp_info(rtsp_url)
                
                # Determinar si es HD basado en el ID del stream
                is_hd = 'HD' in stream_id or 'hd' in stream_id.lower()
                
                # Generar descripción
                description = f"Cámara {stream_id}"
                if channel > 1:
                    description += f" Canal {channel}"
                if is_hd:
                    description += " (HD)"
                
                # Detectar tipo de cámara
                camera_type = self.detect_camera_type(rtsp_url, ip)
                
                camera = Go2RTCCamera(
                    stream_id=stream_id,
                    rtsp_url=rtsp_url,
                    ip_address=ip,
                    username=username,
                    password=password,
                    port=port,
                    channel=channel,
                    subtype=subtype,
                    bitrate=bitrate,
                    fps=fps,
                    is_hd=is_hd,
                    description=description,
                    camera_type=camera_type
                )
                
                cameras.append(camera)
        
        self.cameras = cameras
        return cameras
    
    def get_unique_cameras(self) -> List[Go2RTCCamera]:
        """Retorna cámaras únicas basadas en IP y canal"""
        unique_cameras = {}
        
        for camera in self.cameras:
            # Crear clave única basada en IP y canal
            key = f"{camera.ip_address}_{camera.channel}"
            
            # Si no existe o la actual es HD y la existente no
            if key not in unique_cameras or (camera.is_hd and not unique_cameras[key].is_hd):
                unique_cameras[key] = camera
        
        return list(unique_cameras.values())
    
    def group_cameras_by_ip(self) -> Dict[str, List[Go2RTCCamera]]:
        """Agrupa cámaras por dirección IP"""
        grouped = {}
        
        for camera in self.cameras:
            if camera.ip_address not in grouped:
                grouped[camera.ip_address] = []
            grouped[camera.ip_address].append(camera)
        
        return grouped
    
    def get_statistics(self) -> Dict:
        """Alias para get_camera_statistics para compatibilidad"""
        return self.get_camera_statistics()
    
    def get_camera_statistics(self) -> Dict:
        """Retorna estadísticas de las cámaras parseadas"""
        total_cameras = len(self.cameras)
        unique_ips = len(set(camera.ip_address for camera in self.cameras))
        hd_cameras = len([c for c in self.cameras if c.is_hd])
        multi_channel = len([c for c in self.cameras if c.channel > 1])
        
        return {
            "total_streams": total_cameras,
            "unique_ips": unique_ips,
            "hd_streams": hd_cameras,
            "multi_channel_streams": multi_channel,
            "unique_cameras": len(self.get_unique_cameras())
        }
    
    def export_to_json(self, output_file: str) -> None:
        """Exporta las cámaras a un archivo JSON"""
        import json
        
        cameras_data = []
        for camera in self.cameras:
            cameras_data.append({
                "stream_id": camera.stream_id,
                "rtsp_url": camera.rtsp_url,
                "ip_address": camera.ip_address,
                "username": camera.username,
                "password": camera.password,
                "port": camera.port,
                "channel": camera.channel,
                "subtype": camera.subtype,
                "bitrate": camera.bitrate,
                "fps": camera.fps,
                "is_hd": camera.is_hd,
                "description": camera.description,
                "camera_type": camera.camera_type
            })
        
        export_data = {
            "cameras": cameras_data,
            "statistics": self.get_camera_statistics(),
            "total_cameras": len(cameras_data)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

# Función de utilidad para uso directo
def parse_go2rtc_config(yaml_file_path: str) -> List[Go2RTCCamera]:
    """Función de conveniencia para parsear un archivo go2rtc.yaml"""
    parser = Go2RTCParser(yaml_file_path)
    return parser.parse_cameras()

if __name__ == "__main__":
    # Ejemplo de uso
    parser = Go2RTCParser("go2rtc.yaml")
    cameras = parser.parse_cameras()
    
    print(f"Cámaras encontradas: {len(cameras)}")
    print("\nEstadísticas:")
    stats = parser.get_camera_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nPrimeras 5 cámaras:")
    for camera in cameras[:5]:
        print(f"  {camera.stream_id}: {camera.ip_address} (Canal {camera.channel})")