"""
Endpoints de la API para gestión de cámaras RTSP
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from typing import List, Dict, Any, Optional
import logging
import json
import tempfile
import os

from src.core.models import (
    CameraConfig, CameraResponse, CameraListResponse,
    CameraCreateRequest, CameraUpdateRequest, ErrorResponse,
    Go2RTCImportRequest, Go2RTCImportResponse, Go2RTCCameraInfo
)
from src.infrastructure.services.enhanced_camera_manager import enhanced_camera_manager
from src.infrastructure.services.go2rtc_migrator import Go2RTCMigrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["cameras"])

# Usar el gestor mejorado
camera_manager = enhanced_camera_manager


@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(camera_data: CameraCreateRequest):
    """
    Crear una nueva cámara RTSP
    """
    try:
        # Crear configuración de cámara
        camera_config = CameraConfig(
            id=camera_data.id,
            name=camera_data.name,
            url=camera_data.url,
            type=camera_data.type,
            location=camera_data.location,
            description=camera_data.description,
            resolution=camera_data.resolution,
            fps=camera_data.fps,
            enabled=camera_data.enabled,
            metadata=camera_data.metadata or {}
        )
        
        # Agregar cámara al gestor
        response = await camera_manager.add_camera(camera_config)
        
        logger.info(f"Cámara creada exitosamente: {camera_data.name} ({camera_data.id})")
        return response
        
    except ValueError as e:
        logger.error(f"Error de validación creando cámara: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error interno creando cámara: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/", response_model=CameraListResponse)
async def list_cameras():
    """
    Obtener lista de todas las cámaras
    """
    try:
        response = await camera_manager.list_cameras()
        return response
        
    except Exception as e:
        logger.error(f"Error obteniendo lista de cámaras: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str):
    """
    Obtener información de una cámara específica
    """
    try:
        camera = await camera_manager.get_camera(camera_id)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada"
            )
        
        return camera
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: str, camera_data: CameraUpdateRequest):
    """
    Actualizar configuración de una cámara
    """
    try:
        # Convertir a diccionario excluyendo valores None
        updates = camera_data.model_dump(exclude_unset=True, exclude_none=True)
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron datos para actualizar"
            )
        
        camera = await camera_manager.update_camera(camera_id, updates)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada"
            )
        
        logger.info(f"Cámara actualizada exitosamente: {camera_id}")
        return camera
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación actualizando cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error interno actualizando cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: str):
    """
    Eliminar una cámara
    """
    try:
        success = await camera_manager.remove_camera(camera_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada"
            )
        
        logger.info(f"Cámara eliminada exitosamente: {camera_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interno eliminando cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/enable", response_model=CameraResponse)
async def enable_camera(camera_id: str):
    """
    Habilitar una cámara
    """
    try:
        camera = await camera_manager.update_camera(camera_id, {"enabled": True})
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada"
            )
        
        logger.info(f"Cámara habilitada: {camera_id}")
        return camera
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error habilitando cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/disable", response_model=CameraResponse)
async def disable_camera(camera_id: str):
    """
    Deshabilitar una cámara
    """
    try:
        camera = await camera_manager.update_camera(camera_id, {"enabled": False})
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada"
            )
        
        logger.info(f"Cámara deshabilitada: {camera_id}")
        return camera
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deshabilitando cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/test", response_model=Dict[str, Any])
async def test_camera_connection(camera_id: str):
    """
    Probar conexión con una cámara
    """
    try:
        camera = await camera_manager.get_camera(camera_id)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada"
            )
        
        # Probar conexión
        success = await camera_manager.test_camera_connection(camera_id)
        
        return {
            "camera_id": camera_id,
            "connection_test": "success" if success else "failed",
            "status": camera.status,
            "timestamp": camera.updated_at.isoformat() if camera.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error probando conexión de cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/status", response_model=Dict[str, Any])
async def get_camera_status(camera_id: str):
    """
    Obtener estado detallado de una cámara
    """
    try:
        camera = await camera_manager.get_camera(camera_id)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara con ID {camera_id} no encontrada"
            )
        
        # Obtener sesiones activas para esta cámara
        active_sessions = await camera_manager.get_active_sessions()
        camera_sessions = [s for s in active_sessions if s.camera_id == camera_id]
        
        return {
            "camera_id": camera_id,
            "name": camera.name,
            "status": camera.status,
            "enabled": camera.enabled,
            "active_sessions": len(camera_sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "client_id": s.client_id,
                    "started_at": s.started_at.isoformat(),
                    "is_active": s.is_active
                }
                for s in camera_sessions
            ],
            "last_updated": camera.updated_at.isoformat() if camera.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado de cámara {camera_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/bulk", response_model=List[CameraResponse])
async def create_cameras_bulk(cameras_data: List[CameraCreateRequest]):
    """
    Crear múltiples cámaras en lote
    """
    try:
        results = []
        errors = []
        
        for camera_data in cameras_data:
            try:
                camera_config = CameraConfig(
                    id=camera_data.id,
                    name=camera_data.name,
                    url=camera_data.url,
                    type=camera_data.type,
                    location=camera_data.location,
                    description=camera_data.description,
                    resolution=camera_data.resolution,
                    fps=camera_data.fps,
                    enabled=camera_data.enabled,
                    metadata=camera_data.metadata or {}
                )
                
                response = await camera_manager.add_camera(camera_config)
                results.append(response)
                
            except Exception as e:
                errors.append({
                    "camera_id": camera_data.id,
                    "error": str(e)
                })
        
        if errors:
            logger.warning(f"Errores en creación en lote: {errors}")
        
        logger.info(f"Creación en lote completada: {len(results)} exitosas, {len(errors)} errores")
        return results
        
    except Exception as e:
        logger.error(f"Error en creación en lote: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/import/go2rtc", response_model=Go2RTCImportResponse)
async def import_from_go2rtc(request: Go2RTCImportRequest):
    """Importar cámaras desde un archivo go2rtc.yaml"""
    try:
        # Verificar que el archivo existe
        if not os.path.exists(request.yaml_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Archivo no encontrado: {request.yaml_file_path}"
            )
        
        # Crear migrador
        migrator = Go2RTCMigrator(request.yaml_file_path)
        
        # Ejecutar migración
        summary = await migrator.migrate_all_cameras(
            skip_existing=request.skip_existing
        )
        
        # Convertir a respuesta
        response = Go2RTCImportResponse(
            total_cameras=summary["total_cameras"],
            successful_imports=summary["successful_migrations"],
            failed_imports=summary["failed_migrations"],
            skipped_cameras=0,  # Calculado en el migrador
            import_details=summary["migration_results"],
            statistics=summary["statistics"]
        )
        
        logger.info(f"Importación go2rtc completada: {response.successful_imports} exitosas")
        return response
        
    except Exception as e:
        logger.error(f"Error en importación go2rtc: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


@router.post("/import/go2rtc/upload", response_model=Go2RTCImportResponse)
async def import_from_go2rtc_upload(
    file: UploadFile = File(...),
    skip_existing: bool = True,
    test_connections: bool = False,
    unique_only: bool = True
):
    """Importar cámaras subiendo un archivo go2rtc.yaml"""
    try:
        # Verificar tipo de archivo
        if not file.filename.endswith(('.yaml', '.yml')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="El archivo debe ser un YAML (.yaml o .yml)"
            )
        
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.yaml', delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Crear migrador
            migrator = Go2RTCMigrator(temp_file_path)
            
            # Ejecutar migración
            summary = await migrator.migrate_all_cameras(
                skip_existing=skip_existing
            )
            
            # Convertir a respuesta
            response = Go2RTCImportResponse(
                total_cameras=summary["total_cameras"],
                successful_imports=summary["successful_migrations"],
                failed_imports=summary["failed_migrations"],
                skipped_cameras=0,
                import_details=summary["migration_results"],
                statistics=summary["statistics"]
            )
            
            logger.info(f"Importación go2rtc por upload completada: {response.successful_imports} exitosas")
            return response
            
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error en importación go2rtc por upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


@router.get("/import/go2rtc/preview/{file_path:path}", response_model=List[Go2RTCCameraInfo])
async def preview_go2rtc_import(file_path: str):
    """Previsualizar cámaras que se importarían desde go2rtc.yaml"""
    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Archivo no encontrado: {file_path}"
            )
        
        # Parsear archivo
        from ...infrastructure.services.go2rtc_parser import Go2RTCParser
        parser = Go2RTCParser(file_path)
        cameras = parser.parse_cameras()
        
        # Convertir a respuesta
        camera_info_list = []
        for camera in cameras:
            camera_info = Go2RTCCameraInfo(
                stream_id=camera.stream_id,
                rtsp_url=camera.rtsp_url,
                ip_address=camera.ip_address,
                username=camera.username,
                password=camera.password,
                port=camera.port,
                channel=camera.channel,
                subtype=camera.subtype,
                bitrate=camera.bitrate,
                fps=camera.fps,
                is_hd=camera.is_hd,
                description=camera.description
            )
            camera_info_list.append(camera_info)
        
        return camera_info_list
        
    except Exception as e:
        logger.error(f"Error en preview go2rtc: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )