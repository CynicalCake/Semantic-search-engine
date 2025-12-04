"""
Script de prueba simple para verificar el arreglo de DBpedia Reducida
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.dbpedia_reduced_service import DBpediaReducedService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_expansion():
    """Prueba la expansión con el método arreglado"""
    print("🧪 Probando expansión de DBpedia Reducida...")
    
    try:
        service = DBpediaReducedService()
        current_count = service.get_movie_count()
        
        print(f"📊 Películas actuales: {current_count}")
        
        # Intentar agregar solo 50 películas para prueba rápida
        print("⏳ Intentando agregar 50 películas...")
        added = service.expand_database(50)
        
        final_count = service.get_movie_count()
        print(f"✅ Películas agregadas: {added}")
        print(f"📈 Total final: {final_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

if __name__ == "__main__":
    test_expansion()