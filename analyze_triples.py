#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ontology_service import OntologyService

# Crear instancia del servicio
ontology_file = "OntologiaPeliculasV5.owl"
ontology_service = OntologyService(ontology_file)

print("=== Análisis de Estructura de Triples ===")
print(f"Triples cargados: {len(ontology_service.graph)}")

print("\n=== Algunos triples de ejemplo ===")
count = 0
for subject, predicate, obj in ontology_service.graph:
    if count < 20:  # Solo mostrar los primeros 20 triples
        print(f"S: {subject}")
        print(f"P: {predicate}")
        print(f"O: {obj}")
        print("---")
        count += 1

print("\n=== Buscando propiedades relacionadas con películas ===")
for subject, predicate, obj in ontology_service.graph:
    if 'Avengers' in str(obj):
        print(f"Avengers encontrado:")
        print(f"S: {subject}")
        print(f"P: {predicate}")
        print(f"O: {obj}")
        print("---")