"""
Script simple para probar el servicio de DBpedia reducida
"""

import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.dbpedia_reduced_service import DBpediaReducedService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dbpedia_reduced():
    """Prueba básica del servicio de DBpedia reducida"""
    print("🚀 Iniciando prueba de DBpedia Reducida...")
    
    # Inicializar el servicio
    service = DBpediaReducedService()
    
    print(f"📊 Estado del servicio: {'✅ Activo' if service.health_check() else '❌ Inactivo'}")
    
    # Obtener estadísticas
    stats = service.get_stats()
    print(f"📈 Estadísticas:")
    print(f"   - Películas: {stats['peliculas']}")
    print(f"   - Directores: {stats['directores']}")
    print(f"   - Géneros: {stats['generos']}")
    print(f"   - Total triples: {stats['triples_total']}")
    print(f"   - Última actualización: {stats['ultima_actualizacion']}")
    
    # Realizar una búsqueda de prueba
    if stats['peliculas'] > 0:
        print("\n🔍 Realizando búsqueda de prueba...")
        results = service.search_movies("the", limit=5)
        print(f"📽️ Resultados encontrados: {len(results)}")
        
        for i, movie in enumerate(results, 1):
            print(f"   {i}. {movie['titulo']} ({movie['anio']}) - {movie['director']}")
            
        # Prueba de búsqueda semántica
        print("\n🧠 Realizando búsqueda semántica de prueba...")
        semantic_results = service.search_movies_semantic(genre="Action")
        print(f"🎬 Resultados semánticos: {len(semantic_results)}")
    else:
        print("\n⚠️ No hay datos disponibles para pruebas de búsqueda")
        print("   Es posible que la descarga inicial esté en progreso...")

if __name__ == "__main__":
    test_dbpedia_reduced()