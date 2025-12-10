from services.ontology_service import OntologyService
from services.dbpedia_client import get_movies_from_dbpedia

# Cargar ontología
service = OntologyService("OntologiaVacia.owl")

# Obtener datos reales de DBpedia
dbpedia_data = get_movies_from_dbpedia()  # Aquí se ejecutan los prints de debug

print("DEBUG populate_test - Datos obtenidos de DBpedia:", dbpedia_data)

# Poblar ontología
resultado = service.populate_from_dbpedia(dbpedia_data, save_to="OntologiaPeliculasV5.owl")
print(resultado)
