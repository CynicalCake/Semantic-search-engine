from SPARQLWrapper import SPARQLWrapper, JSON
import logging
from typing import List, Dict, Optional
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)


class DBpediaService:
    """Servicio multilingüe para consultas a DBpedia"""

    def __init__(self, endpoint: str = "http://dbpedia.org/sparql"):
        # Endpoints por idioma
        self.endpoints = {
            'es': 'http://es.dbpedia.org/sparql',
            'en': 'http://dbpedia.org/sparql',
            'fr': 'http://fr.dbpedia.org/sparql',
            'de': 'http://de.dbpedia.org/sparql'
        }

        # Usar el endpoint por defecto o el especificado
        self.default_endpoint = endpoint
        self.timeout = 10

    def get_sparql_wrapper(self, language: str = 'es'):
        """Obtiene el wrapper SPARQL para el idioma especificado"""
        endpoint = self.endpoints.get(language, self.endpoints['es'])
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(self.timeout)
        return sparql

    def search_movies(self, term: str, language: str = "es", limit: int = 20) -> List[Dict]:
        """
        Busca películas en DBpedia en el idioma especificado

        Args:
            term: Término de búsqueda
            language: Código de idioma (es, en, fr, de)
            limit: Número máximo de resultados

        Returns:
            Lista de películas encontradas en DBpedia
        """
        safe_term = term.replace('"', '\\\\"')
        sparql = self.get_sparql_wrapper(language)

        # Query adaptada según idioma
        if language == 'en':
            query = f"""
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbp: <http://dbpedia.org/property/>
                
                SELECT DISTINCT ?pelicula ?titulo ?directorName ?abstract ?releaseDate ?runtime
                WHERE {{
                    ?pelicula a dbo:Film ;
                             rdfs:label ?titulo .
                             
                    OPTIONAL {{ 
                        ?pelicula dbo:director ?director . 
                        ?director rdfs:label ?directorName . 
                        FILTER(lang(?directorName) = "en")
                    }}
                    
                    OPTIONAL {{ 
                        ?pelicula dbo:abstract ?abstract . 
                        FILTER(lang(?abstract) = "en")
                    }}
                    
                    OPTIONAL {{ ?pelicula dbo:releaseDate ?releaseDate }}
                    OPTIONAL {{ ?pelicula dbo:runtime ?runtime }}
                    
                    FILTER regex(?titulo, "{safe_term}", "i")
                    FILTER (lang(?titulo) = "en")
                }}
                ORDER BY ?titulo
                LIMIT {limit}
            """
        else:
            # Query para español, francés, alemán
            query = f"""
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dbp: <http://dbpedia.org/property/>
                
                SELECT DISTINCT ?pelicula ?titulo ?directorName ?abstract ?releaseDate ?runtime
                WHERE {{
                    ?pelicula a dbo:Film ;
                             rdfs:label ?titulo .
                             
                    OPTIONAL {{ 
                        ?pelicula dbo:director ?director . 
                        ?director rdfs:label ?directorName . 
                        FILTER(lang(?directorName) = "{language}" || lang(?directorName) = "en")
                    }}
                    
                    OPTIONAL {{ 
                        ?pelicula dbo:abstract ?abstract . 
                        FILTER(lang(?abstract) = "{language}")
                    }}
                    
                    OPTIONAL {{ ?pelicula dbo:releaseDate ?releaseDate }}
                    OPTIONAL {{ ?pelicula dbo:runtime ?runtime }}
                    
                    FILTER regex(?titulo, "{safe_term}", "i")
                    FILTER (lang(?titulo) = "{language}" || lang(?titulo) = "en")
                }}
                ORDER BY ?titulo
                LIMIT {limit}
            """

        try:
            logger.info(f"Consultando DBpedia {language.upper()}: {term}")
            sparql.setQuery(query)
            results = sparql.query().convert()

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
                        year = release_date.split(
                            "-")[0] if "-" in release_date else release_date
                    except:
                        year = "No disponible"
                else:
                    year = "No disponible"

                # Procesar duración
                runtime = binding.get("runtime", {}).get("value", "")
                if runtime:
                    try:
                        runtime_minutes = int(float(runtime))
                        if runtime_minutes > 1000:
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
                    "fuente": f"DBpedia ({language.upper()})",
                    "tipo": "external",
                    "idioma": language
                }
                movies.append(movie)

            logger.info(
                f"Encontradas {len(movies)} películas en DBpedia para '{term}' ({language})")
            return movies

        except Exception as e:
            logger.error(
                f"Error consultando DBpedia para '{term}' ({language}): {e}")
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
        sparql = self.get_sparql_wrapper(language)

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
            sparql.setQuery(query)
            results = sparql.query().convert()

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
                    "fuente": f"DBpedia ({language.upper()})"
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
        """
        Búsqueda semántica multilingüe en DBpedia

        Args:
            actor: Nombre del actor
            director: Nombre del director
            year: Año de estreno
            genre: Género de la película
            language: Idioma de búsqueda
            limit: Límite de resultados
        """
        try:
            filters = []

            # Filtros adaptados al idioma
            if actor:
                actor_safe = actor.replace('"', '\\"')
                if language == 'en':
                    filters.append(f'?actor rdfs:label "{actor_safe}"@en .')
                else:
                    filters.append(
                        f'?actor rdfs:label "{actor_safe}"@{language} .')
                filters.append(f'?film ?pActor ?actor .')
                filters.append(
                    'FILTER(?pActor IN (dbo:starring, dbo:castMember, dbp:starring, dbo:actor))')

            if director:
                director_safe = director.replace('"', '\\"')
                if language == 'en':
                    filters.append(f'?dir rdfs:label "{director_safe}"@en .')
                else:
                    filters.append(
                        f'?dir rdfs:label "{director_safe}"@{language} .')
                filters.append(f'?film ?pDirector ?dir .')
                filters.append(
                    'FILTER(?pDirector IN (dbo:director, dbp:director))')

            if year:
                filters.append('?film dbo:releaseDate ?rd .')
                filters.append(f'FILTER( STRSTARTS(STR(?rd), "{year}") )')

            if genre:
                genre_safe = genre.replace('"', '\\"')
                filters.append('?film dbo:genre ?g .')
                if language == 'en':
                    filters.append(f'?g rdfs:label "{genre_safe}"@en .')
                else:
                    filters.append(
                        f'?g rdfs:label "{genre_safe}"@{language} .')

            filter_block = "\n".join(filters)

            # Query SPARQL multilingüe
            query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?film ?title ?releaseDate ?runtime ?directorName ?abstract WHERE {{
                ?film rdf:type dbo:Film .
                ?film rdfs:label ?title .
                FILTER(lang(?title) = "{language}" || lang(?title) = "en")

                OPTIONAL {{ ?film dbo:releaseDate ?releaseDate }}
                OPTIONAL {{ ?film dbo:runtime ?runtime }}
                OPTIONAL {{
                    ?film dbo:director ?d .
                    ?d rdfs:label ?directorName .
                    FILTER(lang(?directorName) = "{language}" || lang(?directorName) = "en")
                }}
                OPTIONAL {{
                    ?film dbo:abstract ?abstract .
                    FILTER(lang(?abstract) = "{language}")
                }}

                {filter_block}
            }}
            LIMIT {limit}
            """

            return self._run_sparql(query, language)

        except Exception as e:
            logger.error(
                f"Error en búsqueda semántica DBpedia ({language}): {e}", exc_info=True)
            return []

    def _run_sparql(self, query, language='es'):
        """Ejecuta una consulta SPARQL y procesa los resultados"""
        try:
            endpoint = self.endpoints.get(language, self.endpoints['es'])
            response = requests.get(
                endpoint,
                params={"query": query, "format": "json"},
                timeout=self.timeout
            )
            data = response.json()

            results = []
            for b in data["results"]["bindings"]:
                # Procesar sinopsis
                abstract = b.get("abstract", {}).get("value", "")
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."

                # Procesar año
                release_date = b.get("releaseDate", {}).get("value", "")
                year = "No disponible"
                if release_date:
                    try:
                        year = release_date.split(
                            "-")[0] if "-" in release_date else release_date
                    except:
                        pass

                # Procesar duración
                runtime = b.get("runtime", {}).get("value", "")
                if runtime:
                    try:
                        runtime_minutes = int(float(runtime))
                        if runtime_minutes > 1000:
                            runtime_minutes = runtime_minutes // 60
                        runtime = f"{runtime_minutes} min"
                    except:
                        runtime = "No disponible"
                else:
                    runtime = "No disponible"

                results.append({
                    "uri": b.get("film", {}).get("value"),
                    "titulo": b.get("title", {}).get("value"),
                    "director": b.get("directorName", {}).get("value", "Director no disponible"),
                    "sinopsis": abstract or "Sinopsis no disponible",
                    "anio": year,
                    "duracion": runtime,
                    "fuente": f"DBpedia ({language.upper()})",
                    "tipo": "external",
                    "idioma": language
                })

            return results

        except Exception as e:
            logger.error(
                f"Error en _run_sparql ({language}): {e}", exc_info=True)
            return []

    def search_directors(self, term: str, language: str = "es", limit: int = 5) -> List[Dict]:
        """
        Busca directores en DBpedia multilingüe

        Args:
            term: Término de búsqueda
            language: Idioma preferido
            limit: Número máximo de resultados

        Returns:
            Lista de directores encontrados
        """
        safe_term = term.replace('"', '\\\\"')
        sparql = self.get_sparql_wrapper(language)

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
            sparql.setQuery(query)
            results = sparql.query().convert()

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
                    "fuente": f"DBpedia ({language.upper()})",
                    "idioma": language
                }
                directors.append(director)

            logger.info(
                f"Encontrados {len(directors)} directores en DBpedia para '{term}' ({language})")
            return directors

        except Exception as e:
            logger.error(
                f"Error buscando directores en DBpedia ({language}): {e}")
            return []

    def health_check(self) -> bool:
        """Verifica si DBpedia está disponible"""
        try:
            sparql = self.get_sparql_wrapper('en')
            query = "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"
            sparql.setQuery(query)
            sparql.query().convert()
            return True
        except Exception as e:
            logger.error(f"DBpedia no está disponible: {e}")
            return False
