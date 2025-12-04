"""
Script de configuración inicial para CinemaSearch con DBpedia Reducida

Este script ayuda a configurar el entorno y verificar que todo funcione correctamente.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_requirements():
    """Verifica e instala las dependencias"""
    print("📦 Verificando dependencias...")
    
    try:
        import flask
        import rdflib
        import SPARQLWrapper
        import requests
        print("✅ Todas las dependencias principales están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecutando: pip install -r requirements.txt")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencias instaladas correctamente")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error instalando dependencias")
            return False

def check_ontology_file():
    """Verifica que la ontología local exista"""
    ontology_files = ['OntologiaPeliculasV5.owl', 'OntologiaPeliculasV5.owx']
    
    for filename in ontology_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename) / 1024  # KB
            print(f"✅ Ontología encontrada: {filename} ({size:.1f} KB)")
            return True
    
    print("⚠️ Archivo de ontología no encontrado")
    print("   Archivos esperados: OntologiaPeliculasV5.owl o OntologiaPeliculasV5.owx")
    print("   La aplicación funcionará solo con DBpedia")
    return False

def test_dbpedia_reduced():
    """Prueba el servicio de DBpedia reducida"""
    print("🧪 Probando DBpedia Reducida...")
    
    try:
        # Importar aquí para evitar problemas si las dependencias no están
        from services.dbpedia_reduced_service import DBpediaReducedService
        
        service = DBpediaReducedService()
        stats = service.get_stats()
        current_count = service.get_movie_count()
        
        if stats['peliculas'] > 0:
            print(f"✅ DBpedia Reducida funcionando - {stats['peliculas']:,} películas disponibles")
            
            # Mostrar recomendaciones
            recommendations = service.get_recommended_size()
            print("\n💡 Opciones de expansión disponibles:")
            
            for size, config in recommendations.items():
                if current_count < config['movies']:
                    missing = config['movies'] - current_count
                    print(f"   📈 {size.upper()}: +{missing:,} películas más → {config['movies']:,} total")
                else:
                    print(f"   ✅ {size.upper()}: Ya alcanzado ({config['movies']:,} películas)")
                    
        else:
            print("⚠️ DBpedia Reducida inicializándose - esto puede tomar algunos minutos")
            print("   La descarga se realizará automáticamente al ejecutar la aplicación")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en DBpedia Reducida: {e}")
        return False

def create_startup_info():
    """Crea un archivo con información de configuración"""
    info = f"""# CinemaSearch - Información de Configuración

## Configuración realizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Archivos de datos
- Ontología Local: {'✅ Disponible' if check_ontology_file() else '❌ No encontrada'}
- DBpedia Reducida: Se descargará automáticamente

### Primeros pasos
1. Ejecutar: python app.py
2. Abrir navegador en: http://127.0.0.1:5000
3. Esperar la descarga inicial de DBpedia Reducida (primera vez)

### Funcionalidades
- Búsqueda simple: Ingresar título de película
- Búsqueda semántica: Usar lenguaje natural
- Tres fuentes: Local, DBpedia Online, DBpedia Reducida

### Gestión de Base de Datos
- Configuración inicial: ~2,000 películas (automático)
- Expansión disponible: hasta 10,000+ películas
- Comando de gestión: python manage_dbpedia.py

### Tamaños recomendados:
- Pequeña (500): Desarrollo y pruebas
- Mediana (2,000): Uso académico ⭐ Defecto
- Grande (5,000): Aplicaciones de producción  
- Completa (10,000+): Investigación avanzada

### Expansión rápida:
python manage_dbpedia.py setup [pequeña|mediana|grande|completa]

### Soporte
- README.md: Documentación completa
- test_dbpedia_reduced.py: Pruebas del sistema
"""
    
    with open('CONFIGURACION.md', 'w', encoding='utf-8') as f:
        f.write(info)
    
    print("📄 Archivo CONFIGURACION.md creado con información del sistema")

def main():
    """Función principal del setup"""
    print("🎬 CinemaSearch - Configuración Inicial")
    print("=" * 50)
    
    success = True
    
    # Verificar Python
    if not check_python_version():
        success = False
    
    # Verificar dependencias
    if success and not check_requirements():
        success = False
    
    # Verificar ontología
    check_ontology_file()  # No crítico para el funcionamiento
    
    # Probar DBpedia reducida
    if success:
        test_dbpedia_reduced()
    
    # Crear información
    create_startup_info()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Configuración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("   1. python app.py")
        print("   2. Abrir http://127.0.0.1:5000")
        print("   3. ¡Explorar el buscador de películas!")
        
        if os.path.exists('dbpedia_reduced.ttl'):
            print("\n💡 Tip: La primera búsqueda puede tardar mientras se cargan los datos")
            print("💡 Para más películas: python manage_dbpedia.py")
        else:
            print("\n⏳ Nota: La primera ejecución descargará ~2,000 películas (~5-10 min)")
            print("📈 Para expandir después: python manage_dbpedia.py setup grande")
    else:
        print("❌ Configuración incompleta. Revisa los errores anteriores.")
    
    print("\n📚 Consulta README.md para más información")

if __name__ == "__main__":
    main()