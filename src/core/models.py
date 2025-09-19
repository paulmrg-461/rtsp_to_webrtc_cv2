"""
Modelos de datos para el sistema RTSP to WebRTC
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
from datetime import datetime


class CameraStatus(str, Enum):
    """Estados posibles de una cámara"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class CameraType(str, Enum):
    """Tipos de cámara soportados"""
    RTSP = "rtsp"
    HTTP = "http"
    USB = "usb"
    IP_CAMERA = "ip_camera"
    DAHUA = "dahua"
    HIKVISION = "hikvision"
    AXIS = "axis"
    ONVIF = "onvif"


class CameraConfig(BaseModel):
    """Configuración de una cámara"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Nombre descriptivo de la cámara")
    rtsp_url: str = Field(..., description="URL RTSP de la cámara")
    type: CameraType = Field(default=CameraType.RTSP)
    username: Optional[str] = Field(None, description="Usuario para autenticación")
    password: Optional[str] = Field(None, description="Contraseña para autenticación")
    ip_address: Optional[str] = Field(None, description="Dirección IP de la cámara")
    port: Optional[int] = Field(554, description="Puerto de conexión")
    status: CameraStatus = Field(default=CameraStatus.INACTIVE)
    location: Optional[str] = Field(None, description="Ubicación de la cámara")
    description: Optional[str] = Field(None, description="Descripción adicional")
    resolution: Optional[str] = Field("1920x1080", description="Resolución preferida")
    fps: Optional[int] = Field(30, description="Frames por segundo")
    enabled: bool = Field(True, description="Si la cámara está habilitada")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    settings: Dict[str, Any] = Field(default_factory=dict, description="Configuraciones específicas")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('rtsp_url')
    def validate_rtsp_url(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('URL RTSP no puede estar vacía')
        return v.strip()

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Nombre no puede estar vacío')
        return v.strip()

    class Config:
        use_enum_values = True


class CameraCreateRequest(BaseModel):
    """Solicitud para crear una nueva cámara"""
    id: Optional[str] = None
    name: str = Field(..., description="Nombre descriptivo de la cámara")
    rtsp_url: str = Field(..., description="URL RTSP de la cámara")
    type: CameraType = Field(default=CameraType.RTSP)
    username: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = 554
    location: Optional[str] = None
    description: Optional[str] = None
    resolution: Optional[str] = "1920x1080"
    fps: Optional[int] = 30
    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CameraUpdateRequest(BaseModel):
    """Solicitud para actualizar una cámara existente"""
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    type: Optional[CameraType] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    enabled: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CameraResponse(BaseModel):
    """Respuesta con información de una cámara"""
    id: str
    name: str
    rtsp_url: str
    type: CameraType
    status: CameraStatus
    ip_address: Optional[str]
    port: Optional[int]
    location: Optional[str]
    description: Optional[str]
    resolution: Optional[str]
    fps: Optional[int]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any]
    metadata: Dict[str, Any]

    class Config:
        use_enum_values = True


class CameraListResponse(BaseModel):
    """Response con lista de cámaras"""
    cameras: List[CameraResponse]
    total: int
    active: int
    inactive: int


class StreamSession(BaseModel):
    """Sesión de streaming activa"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    client_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebRTCOffer(BaseModel):
    """Oferta WebRTC"""
    camera_id: str
    client_id: str
    sdp: str
    type: str = "offer"


class WebRTCAnswer(BaseModel):
    """Respuesta WebRTC"""
    session_id: str
    sdp: str
    type: str = "answer"


class ICECandidate(BaseModel):
    """Candidato ICE para WebRTC"""
    session_id: str
    candidate: str
    sdp_mid: Optional[str] = None
    sdp_mline_index: Optional[int] = None


# Modelos específicos para go2rtc
class Go2RTCImportRequest(BaseModel):
    """Solicitud para importar configuración desde go2rtc.yaml"""
    yaml_file_path: str = Field(..., description="Ruta al archivo go2rtc.yaml")
    skip_existing: bool = Field(True, description="Saltar cámaras que ya existen")
    test_connections: bool = Field(False, description="Probar conexiones después de importar")
    unique_only: bool = Field(True, description="Importar solo cámaras únicas por IP y canal")

class Go2RTCImportResponse(BaseModel):
    """Respuesta de la importación desde go2rtc.yaml"""
    total_cameras: int
    successful_imports: int
    failed_imports: int
    skipped_cameras: int
    import_details: List[Dict[str, Any]]
    statistics: Dict[str, Any]

class Go2RTCCameraInfo(BaseModel):
    """Información de una cámara extraída de go2rtc"""
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

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)