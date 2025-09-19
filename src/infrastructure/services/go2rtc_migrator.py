"""
Script de migración para importar cámaras desde go2rtc.yaml al nuevo sistema de gestión
"""
import asyncio
import json
from typing import List, Dict, Optional
from pathlib import Path
import logging

from .go2rtc_parser import Go2RTCParser, Go2RTCCamera
from .enhanced_camera_manager import enhanced_camera_manager
from ...core.models import CameraConfig, CameraCreateRequest, CameraType, CameraStatus

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Go2RTCMigrator:
    """Migrador para importar configuraciones de go2rtc al nuevo sistema"""
    
    def __init__(self, go2rtc_yaml_path: str):
        self.go2rtc_yaml_path = Path(go2rtc_yaml_path)
        self.parser = Go2RTCParser(str(self.go2rtc_yaml_path))
        self.migration_log: List[Dict] = []
        
    def parse_go2rtc_cameras(self) -> List[Go2RTCCamera]:
        """Parsea las cámaras desde el archivo go2rtc.yaml"""
        try:
            cameras = self.parser.parse_cameras()
            logger.info(f"Parseadas {len(cameras)} cámaras desde {self.go2rtc_yaml_path}")
            return cameras
        except Exception as e:
            logger.error(f"Error al parsear go2rtc.yaml: {e}")
            raise
    
    def convert_to_camera_config(self, go2rtc_camera: Go2RTCCamera) -> CameraCreateRequest:
        """Convierte una cámara de go2rtc a CameraCreateRequest"""
        
        # Generar un ID único basado en IP y canal
        camera_id = f"cam_{go2rtc_camera.ip_address.replace('.', '_')}_{go2rtc_camera.channel}"
        if go2rtc_camera.is_hd:
            camera_id += "_hd"
        
        # Generar nombre descriptivo
        name = f"Cámara {go2rtc_camera.ip_address}"
        if go2rtc_camera.channel > 1:
            name += f" Canal {go2rtc_camera.channel}"
        if go2rtc_camera.is_hd:
            name += " HD"
        
        # Configurar tipo de cámara basado en la URL
        camera_type = CameraType.IP_CAMERA
        if "dahua" in go2rtc_camera.rtsp_url.lower():
            camera_type = CameraType.DAHUA
        elif "hikvision" in go2rtc_camera.rtsp_url.lower():
            camera_type = CameraType.HIKVISION
        
        # Crear configuración de cámara
        camera_config = CameraCreateRequest(
            id=camera_id,
            name=name,
            description=go2rtc_camera.description or f"Migrada desde go2rtc - {go2rtc_camera.stream_id}",
            rtsp_url=go2rtc_camera.rtsp_url,
            username=go2rtc_camera.username,
            password=go2rtc_camera.password,
            ip_address=go2rtc_camera.ip_address,
            port=go2rtc_camera.port,
            type=camera_type,
            enabled=True,
            # Configuraciones adicionales
            settings={
                "channel": go2rtc_camera.channel,
                "subtype": go2rtc_camera.subtype,
                "bitrate": go2rtc_camera.bitrate,
                "fps": go2rtc_camera.fps,
                "is_hd": go2rtc_camera.is_hd,
                "go2rtc_stream_id": go2rtc_camera.stream_id,
                "migrated_from": "go2rtc"
            }
        )
        
        return camera_config
    
    async def migrate_camera(self, go2rtc_camera: Go2RTCCamera) -> Dict:
        """Migra una cámara individual al nuevo sistema"""
        migration_result = {
            "go2rtc_stream_id": go2rtc_camera.stream_id,
            "ip_address": go2rtc_camera.ip_address,
            "success": False,
            "error": None,
            "camera_id": None
        }
        
        try:
            # Convertir a configuración del nuevo sistema
            camera_config = self.convert_to_camera_config(go2rtc_camera)
            migration_result["camera_id"] = camera_config.id
            
            # Verificar si la cámara ya existe
            existing_cameras = enhanced_camera_manager.list_cameras()
            if any(cam.id == camera_config.id for cam in existing_cameras):
                logger.warning(f"Cámara {camera_config.id} ya existe, saltando...")
                migration_result["error"] = "Camera already exists"
                return migration_result
            
            # Agregar cámara al nuevo sistema
            result = enhanced_camera_manager.add_camera(camera_config)
            
            if result["success"]:
                migration_result["success"] = True
                logger.info(f"Cámara migrada exitosamente: {camera_config.id}")
                
                # Probar conexión
                try:
                    connection_test = enhanced_camera_manager.test_camera_connection(camera_config.id)
                    if not connection_test["success"]:
                        logger.warning(f"Advertencia: Conexión fallida para {camera_config.id}: {connection_test.get('error')}")
                except Exception as e:
                    logger.warning(f"No se pudo probar conexión para {camera_config.id}: {e}")
            else:
                migration_result["error"] = result.get("error", "Unknown error")
                logger.error(f"Error al migrar cámara {camera_config.id}: {migration_result['error']}")
                
        except Exception as e:
            migration_result["error"] = str(e)
            logger.error(f"Excepción al migrar cámara {go2rtc_camera.stream_id}: {e}")
        
        return migration_result
    
    async def migrate_all_cameras(self, skip_existing: bool = True, test_connections: bool = False) -> Dict:
        """Migra todas las cámaras desde go2rtc al nuevo sistema"""
        logger.info("Iniciando migración de cámaras desde go2rtc...")
        
        # Parsear cámaras
        go2rtc_cameras = self.parse_go2rtc_cameras()
        
        # Obtener cámaras únicas si se especifica
        if skip_existing:
            go2rtc_cameras = self.parser.get_unique_cameras()
            logger.info(f"Usando {len(go2rtc_cameras)} cámaras únicas")
        
        # Migrar cada cámara
        migration_results = []
        successful_migrations = 0
        failed_migrations = 0
        
        for camera in go2rtc_cameras:
            result = await self.migrate_camera(camera)
            migration_results.append(result)
            
            if result["success"]:
                successful_migrations += 1
            else:
                failed_migrations += 1
        
        # Guardar log de migración
        self.migration_log = migration_results
        
        # Generar resumen
        summary = {
            "total_cameras": len(go2rtc_cameras),
            "successful_migrations": successful_migrations,
            "failed_migrations": failed_migrations,
            "migration_results": migration_results,
            "statistics": self.parser.get_camera_statistics()
        }
        
        logger.info(f"Migración completada: {successful_migrations} exitosas, {failed_migrations} fallidas")
        
        return summary
    
    def save_migration_report(self, summary: Dict, output_file: str) -> None:
        """Guarda un reporte detallado de la migración"""
        report = {
            "migration_timestamp": str(asyncio.get_event_loop().time()),
            "source_file": str(self.go2rtc_yaml_path),
            "summary": summary,
            "detailed_results": self.migration_log
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte de migración guardado en: {output_file}")
    
    def rollback_migration(self, migration_results: List[Dict]) -> Dict:
        """Revierte una migración eliminando las cámaras migradas"""
        logger.info("Iniciando rollback de migración...")
        
        rollback_results = []
        successful_rollbacks = 0
        failed_rollbacks = 0
        
        for result in migration_results:
            if result["success"] and result["camera_id"]:
                try:
                    # Eliminar cámara del sistema
                    delete_result = enhanced_camera_manager.remove_camera(result["camera_id"])
                    
                    rollback_result = {
                        "camera_id": result["camera_id"],
                        "success": delete_result["success"],
                        "error": delete_result.get("error")
                    }
                    
                    if delete_result["success"]:
                        successful_rollbacks += 1
                        logger.info(f"Rollback exitoso para cámara: {result['camera_id']}")
                    else:
                        failed_rollbacks += 1
                        logger.error(f"Error en rollback para cámara {result['camera_id']}: {rollback_result['error']}")
                    
                    rollback_results.append(rollback_result)
                    
                except Exception as e:
                    failed_rollbacks += 1
                    rollback_result = {
                        "camera_id": result["camera_id"],
                        "success": False,
                        "error": str(e)
                    }
                    rollback_results.append(rollback_result)
                    logger.error(f"Excepción en rollback para cámara {result['camera_id']}: {e}")
        
        summary = {
            "total_rollbacks": len(rollback_results),
            "successful_rollbacks": successful_rollbacks,
            "failed_rollbacks": failed_rollbacks,
            "rollback_results": rollback_results
        }
        
        logger.info(f"Rollback completado: {successful_rollbacks} exitosos, {failed_rollbacks} fallidos")
        
        return summary

# Funciones de utilidad para uso directo
async def migrate_from_go2rtc(yaml_file_path: str, skip_existing: bool = True) -> Dict:
    """Función de conveniencia para migrar desde go2rtc"""
    migrator = Go2RTCMigrator(yaml_file_path)
    return await migrator.migrate_all_cameras(skip_existing=skip_existing)

def create_migration_script(yaml_file_path: str, output_script: str) -> None:
    """Crea un script de migración personalizado"""
    script_content = f'''#!/usr/bin/env python3
"""
Script de migración generado automáticamente para go2rtc.yaml
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.services.go2rtc_migrator import Go2RTCMigrator

async def main():
    migrator = Go2RTCMigrator("{yaml_file_path}")
    
    print("Iniciando migración desde go2rtc...")
    summary = await migrator.migrate_all_cameras(skip_existing=True)
    
    print(f"\\nResumen de migración:")
    print(f"  Total de cámaras: {{summary['total_cameras']}}")
    print(f"  Migraciones exitosas: {{summary['successful_migrations']}}")
    print(f"  Migraciones fallidas: {{summary['failed_migrations']}}")
    
    # Guardar reporte
    migrator.save_migration_report(summary, "migration_report.json")
    print("\\nReporte guardado en: migration_report.json")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(output_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    logger.info(f"Script de migración creado: {output_script}")

if __name__ == "__main__":
    # Ejemplo de uso
    async def example_migration():
        migrator = Go2RTCMigrator("go2rtc.yaml")
        summary = await migrator.migrate_all_cameras()
        migrator.save_migration_report(summary, "migration_report.json")
        
        print("Migración completada. Ver migration_report.json para detalles.")
    
    asyncio.run(example_migration())