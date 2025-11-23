#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ontology_service import OntologyService

# Crear instancia del servicio
ontology_file = "OntologiaPeliculasV5.owl"
ontology_service = OntologyService(ontology_file)

print("=== Test de Búsqueda Directa ===")
print(f"Triples cargados: {len(ontology_service.graph)}")

# Probar búsqueda directa
print("\n=== Buscando 'Avengers' ===")
avengers_results = ontology_service.search_movies("Avengers", limit=5)
for movie in avengers_results:
    print(f"- {movie['titulo']} ({movie['director']}) [{movie['anio']}]")

print("\n=== Buscando 'Inception' ===")
inception_results = ontology_service.search_movies("Inception", limit=5)
for movie in inception_results:
    print(f"- {movie['titulo']} ({movie['director']}) [{movie['anio']}]")

print("\n=== Estadísticas básicas ===")
stats = ontology_service.get_stats()
print(f"Total triples: {stats.get('total_triples', 0)}")
print(f"Películas: {stats.get('movies_count', 0)}")
print(f"Directores: {stats.get('directors_count', 0)}")