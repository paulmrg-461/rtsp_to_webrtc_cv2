#!/usr/bin/env python3
"""
Script de prueba simplificado para go2rtc.yaml
Solo prueba el parser sin dependencias complejas
"""

import json
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

# Importar solo el parser
from src.infrastructure.services.go2rtc_parser import Go2RTCParser


def test_parser_basic():
    """Probar el parser básico de go2rtc.yaml"""
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
        print(f"\n📹 Primeras 5 cámaras:")
        for i, camera in enumerate(cameras[:5]):
            print(f"   {i+1}. {camera.stream_id}")
            print(f"      RTSP: {camera.rtsp_url}")
            print(f"      IP: {camera.ip_address}")
            print(f"      Puerto: {camera.port}")
            print(f"      Tipo: {camera.camera_type}")
            print(f"      Usuario: {camera.username}")
            print(f"      HD: {camera.is_hd}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en parser: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_json():
    """Probar exportación a JSON"""
    print("📤 Probando exportación a JSON...")
    
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
            
            print(f"✅ Exportación JSON exitosa:")
            print(f"   - Total cámaras: {len(data['cameras'])}")
            print(f"   - Archivo: {json_output}")
            print(f"   - Tamaño: {os.path.getsize(json_output)} bytes")
            
            # Mostrar estructura del primer elemento
            if data['cameras']:
                first_camera = data['cameras'][0]
                print(f"   - Ejemplo estructura:")
                for key in first_camera.keys():
                    print(f"     * {key}")
            
            # Limpiar archivo de prueba
            os.remove(json_output)
            print(f"   - Archivo temporal limpiado")
            
            return True
        else:
            print("❌ Error: archivo JSON no creado")
            return False
        
    except Exception as e:
        print(f"❌ Error en exportación: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_camera_analysis():
    """Analizar tipos y características de las cámaras"""
    print("🎥 Analizando características de las cámaras...")
    
    yaml_file = "go2rtc.yaml"
    if not os.path.exists(yaml_file):
        print(f"❌ Archivo {yaml_file} no encontrado")
        return False
    
    try:
        parser = Go2RTCParser(yaml_file)
        cameras = parser.parse_cameras()
        
        # Análisis por tipos
        type_counts = {}
        ip_counts = {}
        port_counts = {}
        hd_count = 0
        with_credentials = 0
        
        for camera in cameras:
            # Tipos de cámara
            camera_type = camera.camera_type or "UNKNOWN"
            type_counts[camera_type] = type_counts.get(camera_type, 0) + 1
            
            # IPs únicas
            if camera.ip_address:
                ip_counts[camera.ip_address] = ip_counts.get(camera.ip_address, 0) + 1
            
            # Puertos
            if camera.port:
                port_counts[camera.port] = port_counts.get(camera.port, 0) + 1
            
            # HD
            if camera.is_hd:
                hd_count += 1
            
            # Credenciales
            if camera.username and camera.password:
                with_credentials += 1
        
        print(f"📊 Análisis completo:")
        print(f"   - Total cámaras: {len(cameras)}")
        print(f"   - Cámaras HD: {hd_count}")
        print(f"   - Con credenciales: {with_credentials}")
        print(f"   - IPs únicas: {len(ip_counts)}")
        
        print(f"\n🎥 Tipos de cámara:")
        for camera_type, count in sorted(type_counts.items()):
            print(f"   - {camera_type}: {count}")
        
        print(f"\n🌐 Top 5 IPs más usadas:")
        for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {ip}: {count} cámaras")
        
        print(f"\n🔌 Puertos más comunes:")
        for port, count in sorted(port_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {port}: {count} cámaras")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas simplificadas de go2rtc")
    print("=" * 60)
    
    tests = [
        ("Parser básico", test_parser_basic),
        ("Exportación JSON", test_export_json),
        ("Análisis de cámaras", test_camera_analysis),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error crítico en {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado final: {passed}/{len(results)} pruebas exitosas")
    
    if passed == len(results):
        print("🎉 ¡Todas las pruebas pasaron! El parser está funcionando correctamente.")
        print("📝 Próximos pasos:")
        print("   1. Configurar variables de entorno para pruebas completas")
        print("   2. Probar endpoints de API con el servidor corriendo")
        print("   3. Realizar migración real de cámaras")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar errores arriba.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)