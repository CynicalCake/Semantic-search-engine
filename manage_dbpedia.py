"""
Gestor avanzado de DBpedia Reducida
Permite expandir, actualizar y configurar la base de datos de películas.
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.dbpedia_reduced_service import DBpediaReducedService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_status():
    """Muestra el estado actual de la base de datos"""
    print("📊 Estado actual de DBpedia Reducida")
    print("=" * 50)
    
    service = DBpediaReducedService()
    stats = service.get_stats()
    
    print(f"🎬 Películas: {stats['peliculas']:,}")
    print(f"🎭 Directores: {stats['directores']:,}")
    print(f"🎨 Géneros: {stats['generos']:,}")
    print(f"📚 Total triples: {stats['triples_total']:,}")
    print(f"📅 Última actualización: {stats['ultima_actualizacion']}")
    print(f"🏷️ Versión: {stats['version']}")
    
    if service.health_check():
        print("✅ Estado: Funcionando correctamente")
    else:
        print("❌ Estado: Problemas detectados")

def show_recommendations():
    """Muestra recomendaciones de tamaño"""
    print("\n💡 Recomendaciones de Tamaño")
    print("=" * 50)
    
    service = DBpediaReducedService()
    current_count = service.get_movie_count()
    recommendations = service.get_recommended_size()
    
    print(f"📊 Tamaño actual: {current_count:,} películas")
    print("\n🎯 Configuraciones recomendadas:")
    
    for size, config in recommendations.items():
        movies = config['movies']
        desc = config['description']
        
        if current_count >= movies:
            status = "✅ Alcanzado"
        else:
            missing = movies - current_count
            status = f"➕ Faltan {missing:,}"
            
        print(f"   {size.upper()}: {movies:,} películas - {desc} [{status}]")

def expand_database(target_movies: int):
    """Expande la base de datos al tamaño objetivo"""
    print(f"🚀 Expandiendo base de datos a {target_movies:,} películas")
    print("=" * 50)
    
    service = DBpediaReducedService()
    current_count = service.get_movie_count()
    
    if current_count >= target_movies:
        print(f"✅ Ya tienes {current_count:,} películas (objetivo: {target_movies:,})")
        return
    
    needed = target_movies - current_count
    print(f"📈 Películas actuales: {current_count:,}")
    print(f"🎯 Objetivo: {target_movies:,}")
    print(f"➕ Se agregarán: {needed:,} películas")
    
    print("\n⏳ Iniciando descarga... (esto puede tomar varios minutos)")
    
    try:
        added = service.expand_database(needed)
        final_count = service.get_movie_count()
        
        print(f"\n🎉 ¡Expansión completada!")
        print(f"   Películas agregadas: {added:,}")
        print(f"   Total final: {final_count:,}")
        
    except Exception as e:
        print(f"❌ Error durante la expansión: {e}")
        logger.error(f"Error expandiendo: {e}")

def update_database():
    """Actualiza completamente la base de datos"""
    print("🔄 Actualizando base de datos completa")
    print("=" * 50)
    print("⚠️ Esto descargará datos frescos desde DBpedia")
    print("⏳ Tiempo estimado: 5-15 minutos")
    
    confirm = input("\n¿Continuar? (s/N): ").lower().strip()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Actualización cancelada")
        return
    
    try:
        service = DBpediaReducedService()
        service.force_update()
        
        # Mostrar estadísticas finales
        stats = service.get_stats()
        print(f"\n✅ Actualización completada!")
        print(f"   Películas: {stats['peliculas']:,}")
        print(f"   Directores: {stats['directores']:,}")
        print(f"   Triples: {stats['triples_total']:,}")
        
    except Exception as e:
        print(f"❌ Error durante la actualización: {e}")
        logger.error(f"Error actualizando: {e}")

def quick_setup(size: str = "mediana"):
    """Configuración rápida a un tamaño específico"""
    print(f"⚡ Configuración rápida: {size}")
    print("=" * 50)
    
    service = DBpediaReducedService()
    recommendations = service.get_recommended_size()
    
    if size not in recommendations:
        print(f"❌ Tamaño '{size}' no válido")
        print(f"   Opciones: {', '.join(recommendations.keys())}")
        return
    
    target = recommendations[size]['movies']
    description = recommendations[size]['description']
    
    print(f"🎯 Configurando para: {target:,} películas")
    print(f"📝 Descripción: {description}")
    
    expand_database(target)

def search_test(term: str = "batman"):
    """Prueba de búsqueda rápida"""
    print(f"🔍 Probando búsqueda: '{term}'")
    print("=" * 50)
    
    try:
        service = DBpediaReducedService()
        results = service.search_movies(term, limit=5)
        
        print(f"📽️ Resultados encontrados: {len(results)}")
        
        for i, movie in enumerate(results, 1):
            print(f"   {i}. {movie['titulo']} ({movie['anio']})")
            print(f"      Director: {movie['director']}")
            print()
            
        if len(results) == 0:
            print("💡 Tip: Prueba expandir la base de datos para más resultados")
            
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Gestor de DBpedia Reducida')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando status
    subparsers.add_parser('status', help='Muestra el estado actual')
    
    # Comando recommendations
    subparsers.add_parser('recommendations', help='Muestra recomendaciones de tamaño')
    
    # Comando expand
    expand_parser = subparsers.add_parser('expand', help='Expande la base de datos')
    expand_parser.add_argument('movies', type=int, help='Número objetivo de películas')
    
    # Comando update
    subparsers.add_parser('update', help='Actualiza la base de datos completa')
    
    # Comando setup
    setup_parser = subparsers.add_parser('setup', help='Configuración rápida')
    setup_parser.add_argument('size', choices=['pequeña', 'mediana', 'grande', 'completa'], 
                             nargs='?', default='mediana', help='Tamaño objetivo')
    
    # Comando search
    search_parser = subparsers.add_parser('search', help='Prueba de búsqueda')
    search_parser.add_argument('term', nargs='?', default='batman', help='Término a buscar')
    
    args = parser.parse_args()
    
    if not args.command:
        # Modo interactivo si no hay argumentos
        print("🎬 Gestor de DBpedia Reducida - Modo Interactivo")
        print("=" * 50)
        print("1. Ver estado actual")
        print("2. Ver recomendaciones")
        print("3. Configuración rápida (mediana)")
        print("4. Expandir base de datos")
        print("5. Actualizar completamente")
        print("6. Prueba de búsqueda")
        print("0. Salir")
        
        while True:
            choice = input("\nSelecciona una opción (0-6): ").strip()
            
            if choice == '0':
                print("👋 ¡Hasta luego!")
                break
            elif choice == '1':
                show_status()
            elif choice == '2':
                show_recommendations()
            elif choice == '3':
                quick_setup()
            elif choice == '4':
                try:
                    movies = int(input("¿Cuántas películas objetivo? "))
                    expand_database(movies)
                except ValueError:
                    print("❌ Por favor ingresa un número válido")
            elif choice == '5':
                update_database()
            elif choice == '6':
                term = input("Término de búsqueda (Enter para 'batman'): ").strip() or "batman"
                search_test(term)
            else:
                print("❌ Opción no válida")
    else:
        # Modo línea de comandos
        if args.command == 'status':
            show_status()
        elif args.command == 'recommendations':
            show_recommendations()
        elif args.command == 'expand':
            expand_database(args.movies)
        elif args.command == 'update':
            update_database()
        elif args.command == 'setup':
            quick_setup(args.size)
        elif args.command == 'search':
            search_test(args.term)

if __name__ == "__main__":
    main()