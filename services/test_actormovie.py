from services.dbpedia_service import DBpediaService

service = DBpediaService()

print("Buscando películas de Johnny Depp...")
results = service.search_movies_by_actor("Johnny Depp")

print("\nRESULTADOS ENCONTRADOS:")
for movie in results:
    print(f"- {movie['titulo']} ({movie['anio']}) → {movie['uri']}")
