#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from services.ner_service import NERService

def test_genre_detection():
    ner = NERService()
    
    # Test Spanish genre detection
    test_queries = [
        'películas de comedia con Tom Hanks',
        'busco terror y ciencia ficción', 
        'drama romántico',
        'animación familiar',
        'thriller de acción'
    ]

    print("Testing Spanish genre detection:")
    print("=" * 50)
    
    for query in test_queries:
        result = ner.extract_all(query, 'es')
        print(f'Query: {query}')
        print(f'Genres: {result["genres"]}')
        print(f'Persons: {result["persons"]}')
        print('-' * 30)

if __name__ == "__main__":
    test_genre_detection()