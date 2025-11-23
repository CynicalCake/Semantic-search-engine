# Test para verificar que funcionen las consultas localmente
from rdflib import Graph

def test_local_ontology():
    try:
        graph = Graph()
        graph.parse('OntologiaPeliculasV5.owl', format='xml')
        
        print(f"Triples cargados: {len(graph)}")
        
        # Query simple
        query = """
            PREFIX onto: <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT DISTINCT ?pelicula ?titulo
            WHERE {
                ?pelicula rdf:type onto:Pelicula .
                ?pelicula onto:nombrePelicula ?titulo .
            }
            LIMIT 5
        """
        
        results = list(graph.query(query))
        print(f"Películas encontradas: {len(results)}")
        
        for i, row in enumerate(results):
            print(f"{i+1}. {row[1]} ({row[0]})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_local_ontology()