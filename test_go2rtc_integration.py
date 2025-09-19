#!/usr/bin/env python3
"""
Script de prueba para la integración con go2rtc.yaml
Prueba el parser, migrador y endpoints de importación
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from src.infrastructure.services.go2rtc_parser import Go2RTCParser
from src.infrastructure.services.go2rtc_migrator import Go2RTCMigrator
from src.core.models import CameraCreateRequest


async def test_parser():
    """Probar el parser de go2rtc.yaml"""
    print("🔍 Probando parser de go2rtc.yaml...")
    
    yaml_file = "go2rtc.yaml"
    if not os.path.exists(yaml_file):
        print(f"❌ Archivo {yaml_file} no encontrado")
        return False
    
    try:
        parser = Go2RTCParser(yaml_file)
        cameras = parser.parse_cameras()
        
        print(f"✅ Parser exitoso: {len(cameras)} cámaras encontradas")
        
        # Mostrar estadísticas
        stats = parser.get_statistics()
        print(f"📊 Estadísticas:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        # Mostrar algunas cámaras de ejemplo
        print(f"\n📹 Primeras 3 cámaras:")
        for i, camera in enumerate(cameras[:3]):
            print(f"   {i+1}. {camera.stream_id} -> {camera.rtsp_url}")
            print(f"      IP: {camera.ip_address}, Puerto: {camera.port}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en parser: {e}")
        return False


async def test_migrator():
    """Probar el migrador de cámaras"""
    print("\n🔄 Probando migrador de cámaras...")
    
    yaml_file = "go2rtc.yaml"
    if not os.path.exists(yaml_file):
        print(f"❌ Archivo {yaml_file} no encontrado")
        return False
    
    try:
        migrator = Go2RTCMigrator(yaml_file)
        
        # Probar conversión sin migrar realmente
        parser = Go2RTCParser(yaml_file)
        cameras = parser.parse_cameras()
        
        converted_cameras = []
        for camera in cameras[:5]:  # Solo las primeras 5 para prueba
            try:
                camera_request = migrator._convert_to_camera_request(camera)
                converted_cameras.append(camera_request)
                print(f"✅ Convertida: {camera.stream_id}")
            except Exception as e:
                print(f"❌ Error convirtiendo {camera.stream_id}: {e}")
        
        print(f"✅ Migrador exitoso: {len(converted_cameras)} cámaras convertidas")
        
        # Mostrar ejemplo de conversión
        if converted_cameras:
            example = converted_cameras[0]
            print(f"\n📝 Ejemplo de conversión:")
            print(f"   ID: {example.id}")
            print(f"   Nombre: {example.name}")
            print(f"   RTSP URL: {example.rtsp_url}")
            print(f"   IP: {example.ip_address}")
            print(f"   Tipo: {example.type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en migrador: {e}")
        return False


async def test_export_functions():
    """Probar funciones de exportación"""
    print("\n📤 Probando funciones de exportación...")
    
    yaml_file = "go2rtc.yaml"
    if not os.path.exists(yaml_file):
        print(f"❌ Archivo {yaml_file} no encontrado")
        return False
    
    try:
        parser = Go2RTCParser(yaml_file)
        
        # Exportar a JSON
        json_output = "test_cameras_export.json"
        parser.export_to_json(json_output)
        
        if os.path.exists(json_output):
            with open(json_output, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Exportación JSON exitosa: {len(data['cameras'])} cámaras")
            
            # Limpiar archivo de prueba
            os.remove(json_output)
        else:
            print("❌ Error: archivo JSON no creado")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en exportación: {e}")
        return False


async def test_camera_types():
    """Probar detección de tipos de cámara"""
    print("\n🎥 Probando detección de tipos de cámara...")
    
    yaml_file = "go2rtc.yaml"
    if not os.path.exists(yaml_file):
        print(f"❌ Archivo {yaml_file} no encontrado")
        return False
    
    try:
        parser = Go2RTCParser(yaml_file)
        cameras = parser.parse_cameras()
        
        # Contar tipos de cámara
        type_counts = {}
        for camera in cameras:
            camera_type = camera.camera_type or "UNKNOWN"
            type_counts[camera_type] = type_counts.get(camera_type, 0) + 1
        
        print(f"📊 Tipos de cámara detectados:")
        for camera_type, count in type_counts.items():
            print(f"   - {camera_type}: {count} cámaras")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en detección de tipos: {e}")
        return False


async def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de integración go2rtc")
    print("=" * 50)
    
    tests = [
        ("Parser", test_parser),
        ("Migrador", test_migrator),
        ("Exportación", test_export_functions),
        ("Tipos de cámara", test_camera_types),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error crítico en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado final: {passed}/{len(results)} pruebas exitosas")
    
    if passed == len(results):
        print("🎉 ¡Todas las pruebas pasaron! La integración está lista.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar errores arriba.")
    
    return passed == len(results)


if __name__ == "__main__":
    asyncio.run(main())