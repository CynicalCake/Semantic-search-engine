#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_search_endpoints():
    """Test los endpoints de búsqueda de la aplicación Flask"""
    base_url = "http://localhost:5000"
    
    print("=== Test de Endpoints de Búsqueda ===")
    
    # Test endpoint debug
    try:
        print("\n1. Probando endpoint de debug...")
        response = requests.get(f"{base_url}/api/debug/graph-status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug OK - Triples: {data.get('triples_count', 0)}")
        else:
            print(f"❌ Debug Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando debug: {e}")
    
    # Test búsqueda
    try:
        print("\n2. Probando búsqueda de Avengers...")
        search_data = {"query": "Avengers", "sources": ["local", "dbpedia"]}
        response = requests.post(f"{base_url}/api/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Búsqueda OK - {len(results.get('results', []))} resultados")
            
            # Mostrar algunos resultados
            for i, movie in enumerate(results.get('results', [])[:3]):
                print(f"  {i+1}. {movie.get('titulo')} - {movie.get('fuente')}")
        else:
            print(f"❌ Búsqueda Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error conectando búsqueda: {e}")

    # Test query local específica
    try:
        print("\n3. Probando query test...")
        response = requests.get(f"{base_url}/api/debug/test-query")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test Query OK - Encontradas: {len(data.get('results', []))}")
        else:
            print(f"❌ Test Query Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error conectando test: {e}")

if __name__ == "__main__":
    test_search_endpoints()