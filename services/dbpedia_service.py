from SPARQLWrapper import SPARQLWrapper, JSON
import logging
from typing import List, Dict, Optional
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

class DBpediaService:
    """Servicio para consultas a DBpedia"""
    
    def __init__(self, endpoint: str = "http://dbpedia.org/sparql"):
        self.endpoint = endpoint
        self.sparql = SPARQLWrapper(endpoint)
        self.sparql.setReturnFormat(JSON)
        
    def search_movies(self, term: str, language: str = "es", limit: int = 20) -> List[Dict]:
        """
        Busca películas en DBpedia
        
        Args:
            term: Término de búsqueda
            language: Código de idioma (es, en, fr, etc.)
            limit: Número máximo de resultados
            
        Returns:
            Lista de películas encontradas en DBpedia
        """
        # Escapar término para SPARQL
        safe_term = term.replace('"', '\\\\"')
        
        query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dbp: <http://dbpedia.org/property/>
            
            SELECT DISTINCT ?pelicula ?titulo ?directorName ?abstract ?releaseDate ?runtime
            WHERE {{
                ?pelicula a dbo:Film ;
                         rdfs:label ?titulo .
                         
                # Director opcional
                OPTIONAL {{ 
                    ?pelicula dbo:director ?director . 
                    ?director rdfs:label ?directorName . 
                    FILTER(lang(?directorName) = "en" || lang(?directorName) = "{language}")
                }}
                
                # Resumen opcional
                OPTIONAL {{ 
                    ?pelicula dbo:abstract ?abstract . 
                    FILTER(lang(?abstract) = "{language}")
                }}
                
                # Fecha de estreno opcional
                OPTIONAL {{ ?pelicula dbo:releaseDate ?releaseDate }}
                
                # Duración opcional
                OPTIONAL {{ ?pelicula dbo:runtime ?runtime }}
                
                # Filtros de búsqueda y idioma
                FILTER regex(?titulo, "{safe_term}", "i")
                FILTER (lang(?titulo) = "{language}" || lang(?titulo) = "en")
            }}
            ORDER BY ?titulo
            LIMIT {limit}
        """
        
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            movies = []
            for binding in results["results"]["bindings"]:
                # Procesar abstract
                abstract = binding.get("abstract", {}).get("value", "")
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."
                
                # Procesar fecha
                release_date = binding.get("releaseDate", {}).get("value", "")
                if release_date:
                    try:
                        # Extraer solo el año si es una fecha completa
                        year = release_date.split("-")[0] if "-" in release_date else release_date
                    except:
                        year = "No disponible"
                else:
                    year = "No disponible"
                
                # Procesar duración
                runtime = binding.get("runtime", {}).get("value", "")
                if runtime:
                    try:
                        # Convertir a minutos si está en segundos
                        runtime_minutes = int(float(runtime))
                        if runtime_minutes > 1000:  # Probablemente en segundos
                            runtime_minutes = runtime_minutes // 60
                        runtime = f"{runtime_minutes} min"
                    except:
                        runtime = "No disponible"
                else:
                    runtime = "No disponible"
                
                movie = {
                    "titulo": binding["titulo"]["value"],
                    "director": binding.get("directorName", {}).get("value", "Director no disponible"),
                    "sinopsis": abstract or "Sinopsis no disponible",
                    "anio": year,
                    "duracion": runtime,
                    "uri": binding["pelicula"]["value"],
                    "fuente": "DBpedia",
                    "tipo": "external"
                }
                movies.append(movie)
            
            logger.info(f"Encontradas {len(movies)} películas en DBpedia para '{term}' ({language})")
            print(movies)
            return movies
            
        except Exception as e:
            logger.error(f"Error consultando DBpedia para '{term}': {e}")
            return []
    
    def get_movie_details(self, movie_uri: str, language: str = "es") -> Optional[Dict]:
        """
        Obtiene detalles completos de una película desde DBpedia
        
        Args:
            movie_uri: URI de la película en DBpedia
            language: Idioma preferido
            
        Returns:
            Detalles de la película o None si no se encuentra
        """
        query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            
            SELECT DISTINCT ?titulo ?directorName ?abstract ?releaseDate ?runtime 
                           ?genre ?country ?budget ?gross ?language
            WHERE {{
                <{movie_uri}> rdfs:label ?titulo .
                
                OPTIONAL {{ <{movie_uri}> dbo:director ?director . ?director rdfs:label ?directorName . }}
                OPTIONAL {{ <{movie_uri}> dbo:abstract ?abstract . FILTER(lang(?abstract) = "{language}") }}
                OPTIONAL {{ <{movie_uri}> dbo:releaseDate ?releaseDate }}
                OPTIONAL {{ <{movie_uri}> dbo:runtime ?runtime }}
                OPTIONAL {{ <{movie_uri}> dbo:genre ?genreUri . ?genreUri rdfs:label ?genre . }}
                OPTIONAL {{ <{movie_uri}> dbo:country ?countryUri . ?countryUri rdfs:label ?country . }}
                OPTIONAL {{ <{movie_uri}> dbo:budget ?budget }}
                OPTIONAL {{ <{movie_uri}> dbo:gross ?gross }}
                OPTIONAL {{ <{movie_uri}> dbo:language ?langUri . ?langUri rdfs:label ?language . }}
                
                FILTER (lang(?titulo) = "{language}" || lang(?titulo) = "en")
            }}
            LIMIT 1
        """
        
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            if results["results"]["bindings"]:
                binding = results["results"]["bindings"][0]
                
                return {
                    "titulo": binding.get("titulo", {}).get("value", "No disponible"),
                    "director": binding.get("directorName", {}).get("value", "No disponible"),
                    "sinopsis": binding.get("abstract", {}).get("value", "No disponible"),
                    "anio": binding.get("releaseDate", {}).get("value", "No disponible"),
                    "duracion": binding.get("runtime", {}).get("value", "No disponible"),
                    "genero": binding.get("genre", {}).get("value", "No disponible"),
                    "pais": binding.get("country", {}).get("value", "No disponible"),
                    "presupuesto": binding.get("budget", {}).get("value", "No disponible"),
                    "recaudacion": binding.get("gross", {}).get("value", "No disponible"),
                    "idioma": binding.get("language", {}).get("value", "No disponible"),
                    "uri": movie_uri,
                    "fuente": "DBpedia"
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo detalles de {movie_uri}: {e}")
            
        return None
    
    def search_movies_semantic(
        self,
        actor=None,
        director=None,
        year=None,
        genre=None,
        language: str = "es",
        limit: int = 20
    ):
        try:
            filters = []

            # --- FILTRO POR ACTOR ---
            if actor:
                actor_safe = actor.replace('"', '\\"')
                filters.append(f'?actor rdfs:label "{actor_safe}"@{language} .')
                filters.append(f'?film ?pActor ?actor .')
                filters.append('FILTER(?pActor IN (dbo:starring, dbo:castMember, dbp:starring, dbo:actor))')

            # --- FILTRO POR DIRECTOR ---
            if director:
                director_safe = director.replace('"', '\\"')
                filters.append(f'?dir rdfs:label "{director_safe}"@{language} .')
                filters.append(f'?film dbo:director ?dir .')

            # --- FILTRO POR AÑO ---
            if year:
                filters.append('?film dbo:releaseDate ?rd .')
                filters.append(f'FILTER( STRSTARTS(STR(?rd), "{year}") )')

            # --- FILTRO POR GÉNERO ---
            if genre:
                genre_safe = genre.replace('"', '\\"')
                filters.append('?film dbo:genre ?g .')
                filters.append(f'?g rdfs:label "{genre_safe}"@{language} .')

            filter_block = "\n".join(filters)

            # SPARQL FINAL
            query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?film ?title ?releaseDate ?runtime ?directorName WHERE {{
                ?film rdf:type dbo:Film .
                ?film rdfs:label ?title .
                FILTER(lang(?title) = "{language}")

                OPTIONAL {{ ?film dbo:releaseDate ?releaseDate }}
                OPTIONAL {{ ?film dbo:runtime ?runtime }}
                OPTIONAL {{
                    ?film dbo:director ?d .
                    ?d rdfs:label ?directorName .
                    FILTER(lang(?directorName) = "{language}")
                }}

                {filter_block}
            }}
            LIMIT {limit}
            """

            return self._run_sparql(query)

        except Exception as e:
            logger.error(f"Error en dbpedia search_movies_by_actor('{actor}') : {e}", exc_info=True)
            return []

    def _run_sparql(self, query):
        try:
            response = requests.get(
                "https://dbpedia.org/sparql",
                params={"query": query, "format": "json"},
                timeout=8
            )
            data = response.json()

            results = []
            for b in data["results"]["bindings"]:
                results.append({
                    "uri": b.get("film", {}).get("value"),
                    "titulo": b.get("title", {}).get("value"),
                    "director": b.get("directorName", {}).get("value"),
                    "anio": b.get("releaseDate", {}).get("value"),
                    "duracion": b.get("runtime", {}).get("value"),
                    "fuente": "DBpedia"
                })

            return results

        except Exception as e:
            logger.error(f"Error en _run_sparql: {e}", exc_info=True)
            return []

    def search_directors(self, term: str, language: str = "es", limit: int = 5) -> List[Dict]:
        """
        Busca directores en DBpedia
        
        Args:
            term: Término de búsqueda
            language: Idioma preferido
            limit: Número máximo de resultados
            
        Returns:
            Lista de directores encontrados
        """
        safe_term = term.replace('"', '\\\\"')
        
        query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?director ?nombre ?abstract ?birthDate
            WHERE {{
                ?director a dbo:FilmDirector ;
                         rdfs:label ?nombre .
                         
                OPTIONAL {{ 
                    ?director dbo:abstract ?abstract . 
                    FILTER(lang(?abstract) = "{language}")
                }}
                OPTIONAL {{ ?director dbo:birthDate ?birthDate }}
                
                FILTER regex(?nombre, "{safe_term}", "i")
                FILTER (lang(?nombre) = "{language}" || lang(?nombre) = "en")
            }}
            ORDER BY ?nombre
            LIMIT {limit}
        """
        
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            directors = []
            for binding in results["results"]["bindings"]:
                abstract = binding.get("abstract", {}).get("value", "")
                if len(abstract) > 200:
                    abstract = abstract[:197] + "..."
                
                director = {
                    "nombre": binding["nombre"]["value"],
                    "biografia": abstract or "Biografía no disponible",
                    "nacimiento": binding.get("birthDate", {}).get("value", "No disponible"),
                    "uri": binding["director"]["value"],
                    "fuente": "DBpedia"
                }
                directors.append(director)
            
            logger.info(f"Encontrados {len(directors)} directores en DBpedia para '{term}'")
            return directors
            
        except Exception as e:
            logger.error(f"Error buscando directores en DBpedia: {e}")
            return []
    
    def health_check(self) -> bool:
        """Verifica si DBpedia está disponible"""
        try:
            # Consulta simple para verificar conectividad
            query = "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"
            self.sparql.setQuery(query)
            self.sparql.query().convert()
            return True
        except Exception as e:
            logger.error(f"DBpedia no está disponible: {e}")
            return False