from rdflib import Graph, Namespace
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OntologyService:
    """Servicio para manejar consultas a la ontología local"""
    
    def __init__(self, ontology_file: str):
        self.ontology_file = ontology_file
        self.graph = Graph()
        self.namespace = Namespace("http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#")
        self._load_ontology()
    
    def _load_ontology(self) -> None:
        """Carga la ontología desde el archivo OWL/OWX"""
        try:
            # Intentar diferentes formatos comunes para archivos OWL/OWX
            formats_to_try = ['xml', 'turtle', 'n3', 'nt']
            
            for format_name in formats_to_try:
                try:
                    self.graph.parse(self.ontology_file, format=format_name)
                    logger.info(f"Ontología cargada exitosamente usando formato {format_name}: {len(self.graph)} triples")
                    return
                except Exception as format_error:
                    logger.debug(f"Falló carga con formato {format_name}: {format_error}")
                    continue
            
            # Si todos los formatos fallan, intentar sin especificar formato
            self.graph.parse(self.ontology_file)
            logger.info(f"Ontología cargada exitosamente con formato automático: {len(self.graph)} triples")
            
        except Exception as e:
            logger.error(f"Error cargando ontología {self.ontology_file}: {e}")
            # No lanzar excepción, permitir que la app funcione solo con DBpedia
            logger.warning("La aplicación continuará funcionando solo con resultados de DBpedia")
    
    def search_movies(self, term: str, limit: int = 10) -> List[Dict]:
        """
        Busca películas en la ontología local por título
        
        Args:
            term: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Lista de películas encontradas
        """
        # Verificar si la ontología se cargó correctamente
        if len(self.graph) == 0:
            logger.warning("La ontología local no está disponible, devolviendo lista vacía")
            return []
            
        query = f"""
            PREFIX : <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
            SELECT DISTINCT ?titulo ?directorName ?sinopsis ?anio ?genero
            WHERE {{
                ?pelicula a :Pelicula .
                ?pelicula :nombrePelicula ?titulo .
                OPTIONAL {{ ?pelicula :dirigidaPor ?director . ?director :nombrePersona ?directorName }}
                OPTIONAL {{ ?pelicula :sinopsisPelicula ?sinopsis }}
                OPTIONAL {{ ?pelicula :anioEstreno ?anio }}
                OPTIONAL {{ ?pelicula :genero ?genero }}
                FILTER regex(?titulo, "{term}", "i")
            }}
            LIMIT {limit}
        """
        
        try:
            results = self.graph.query(query)
            movies = []
            
            for row in results:
                movie = {
                    "titulo": str(row.titulo) if row.titulo else "Sin título",
                    "director": str(row.directorName) if row.directorName else "Director no disponible",
                    "sinopsis": str(row.sinopsis) if row.sinopsis else "Sinopsis no disponible",
                    "anio": str(row.anio) if row.anio else "Año no disponible",
                    "genero": str(row.genero) if row.genero else "Género no disponible",
                    "fuente": "Ontología Local",
                    "tipo": "local"
                }
                movies.append(movie)
            
            logger.info(f"Encontradas {len(movies)} películas locales para '{term}'")
            return movies
            
        except Exception as e:
            logger.error(f"Error en búsqueda local para '{term}': {e}")
            return []
    
    def get_movie_details(self, movie_uri: str) -> Optional[Dict]:
        """Obtiene detalles completos de una película específica"""
        query = f"""
            PREFIX : <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
            SELECT ?titulo ?directorName ?sinopsis ?anio ?genero ?duracion ?idioma
            WHERE {{
                <{movie_uri}> a :Pelicula .
                <{movie_uri}> :nombrePelicula ?titulo .
                OPTIONAL {{ <{movie_uri}> :dirigidaPor ?director . ?director :nombrePersona ?directorName }}
                OPTIONAL {{ <{movie_uri}> :sinopsisPelicula ?sinopsis }}
                OPTIONAL {{ <{movie_uri}> :anioEstreno ?anio }}
                OPTIONAL {{ <{movie_uri}> :genero ?genero }}
                OPTIONAL {{ <{movie_uri}> :duracion ?duracion }}
                OPTIONAL {{ <{movie_uri}> :idioma ?idioma }}
            }}
        """
        
        try:
            results = list(self.graph.query(query))
            if results:
                row = results[0]
                return {
                    "titulo": str(row.titulo) if row.titulo else "Sin título",
                    "director": str(row.directorName) if row.directorName else "No disponible",
                    "sinopsis": str(row.sinopsis) if row.sinopsis else "No disponible",
                    "anio": str(row.anio) if row.anio else "No disponible",
                    "genero": str(row.genero) if row.genero else "No disponible",
                    "duracion": str(row.duracion) if row.duracion else "No disponible",
                    "idioma": str(row.idioma) if row.idioma else "No disponible",
                    "fuente": "Ontología Local"
                }
        except Exception as e:
            logger.error(f"Error obteniendo detalles de película {movie_uri}: {e}")
        
        return None
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas básicas de la ontología"""
        try:
            # Si la ontología no se cargó, retornar estadísticas básicas
            if len(self.graph) == 0:
                return {
                    "total_triples": 0,
                    "total_peliculas": 0,
                    "total_directores": 0,
                    "archivo_ontologia": self.ontology_file,
                    "status": "No cargada - funcionando solo con DBpedia"
                }
            
            # Contar películas
            movies_query = """
                PREFIX : <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
                SELECT (COUNT(?p) as ?count) WHERE { ?p a :Pelicula }
            """
            
            # Contar directores
            directors_query = """
                PREFIX : <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
                SELECT (COUNT(DISTINCT ?d) as ?count) WHERE { 
                    ?p a :Pelicula . 
                    ?p :dirigidaPor ?d 
                }
            """
            
            movies_result = list(self.graph.query(movies_query))
            directors_result = list(self.graph.query(directors_query))
            
            return {
                "total_triples": len(self.graph),
                "total_peliculas": int(movies_result[0].count) if movies_result else 0,
                "total_directores": int(directors_result[0].count) if directors_result else 0,
                "archivo_ontologia": self.ontology_file,
                "status": "Cargada correctamente"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                "total_triples": 0,
                "total_peliculas": 0,
                "total_directores": 0,
                "archivo_ontologia": self.ontology_file,
                "error": str(e),
                "status": "Error"
            }