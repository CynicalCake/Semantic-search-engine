from SPARQLWrapper import SPARQLWrapper, JSON
from services.tmdb_service import TMDBService
import logging
from typing import List, Dict, Optional
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time



logger = logging.getLogger(__name__)
tmdb_service = TMDBService(api_key="a6e641c79b947ea3f97330b3b9928daf")


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
        self.dbpedia_cache = {}  # cache simple en memoria
        self.tmdb_cache = {}     # cache simple en memoria
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
        studio=None,
        language: str = "es",
        limit: int = 10
    ):
    
        try:
            filters = []

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
                    'FILTER(?pDirector IN (dbo:director, dbp:director, dbo:cinematography))')

            if year:
                filters.append('?film dbo:releaseDate ?rd .')
                filters.append(f'FILTER( STRSTARTS(STR(?rd), "{year}") )')

            if genre:
                genre_safe = genre.replace('"', '\\"')
                genre_property_by_lang = {
                    'en': 'dbo:genre',
                    'es': 'prop-es:género',
                    'fr': 'prop-fr:genre',
                    'de': 'prop-de:genre'
                }
                if language in genre_property_by_lang:
                    genre_prop = genre_property_by_lang[language]
                    filters.append(f'?film {genre_prop} ?genreURI .')
                    if language == 'en':
                        filters.append('?genreURI rdfs:label ?genero .')
                    else:
                        filters.append('BIND(?genreURI AS ?genero)')
                    if language == 'en':
                        filters.append('FILTER(lang(?genero) = "en")')
                    else:
                        filters.append(f'FILTER(lang(?genero) = "{language}" || lang(?genero) = "" )')
                    filters.append(
                        f'FILTER(regex(lcase(str(?genero)), lcase("{genre_safe}"), "i"))'
                    )
                else:
                    filters.append('?film dbo:genre ?genreURI .')
                    filters.append('?genreURI rdfs:label ?genero .')
                    filters.append(f'FILTER(lang(?genero) = "{language}")')
                    filters.append(
                        f'FILTER(regex(lcase(str(?genero)), lcase("{genre_safe}"), "i"))'
                    )

            if studio:
                studio_safe = studio.replace('"', '\\"')
                if language == 'en':
                    filters.append(f'?studio rdfs:label "{studio_safe}"@en .')
                else:
                    filters.append(
                        f'?studio rdfs:label "{studio_safe}"@{language} .')
                filters.append(f'?film ?pStudio ?studio .')
                filters.append(
                    'FILTER(?pStudio IN (dbp:company, dbo:distributor))')

            filter_block = "\n".join(filters)

            # Query SPARQL multilingüe
            query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX prop-es: <http://es.dbpedia.org/property/>
            PREFIX prop-fr: <http://fr.dbpedia.org/property/>
            PREFIX prop-en: <http://dbpedia.org/property/>
            
            SELECT DISTINCT ?film ?title ?releaseDate ?runtime
                (GROUP_CONCAT(DISTINCT ?directorName; SEPARATOR=", ") AS ?directores)
                (GROUP_CONCAT(DISTINCT ?actorName; SEPARATOR=", ") AS ?actores)
                (GROUP_CONCAT(DISTINCT ?generoName; SEPARATOR=", ") AS ?generos)
                (SAMPLE(?abstract) AS ?abstract)
            WHERE {{
                ?film rdf:type dbo:Film .
                ?film rdfs:label ?title .
                FILTER(lang(?title) = "{language}" || lang(?title) = "en")

                OPTIONAL {{ ?film dbo:releaseDate ?releaseDate }}
                OPTIONAL {{ ?film dbo:runtime ?runtime }}

                # Directores
                OPTIONAL {{
                    ?film ?pDirector ?d .
                    FILTER(?pDirector IN (dbo:director, dbp:director, dbo:cinematography, dbp:directedBy))
                    ?d rdfs:label ?directorName .
                    FILTER(lang(?directorName) = "{language}" || lang(?directorName) = "en")
                }}

                # Actores
                OPTIONAL {{
                    ?film ?pActores ?actores .
                    FILTER(?pActores IN (dbo:starring, dbo:castMember, dbp:starring, dbo:actor))
                    ?actores rdfs:label ?actorName .
                    FILTER(lang(?actorName) = "{language}" || lang(?actorName) = "en")
                }}

                # Géneros
                OPTIONAL {{
                    ?film ?pGenero ?generoURI .
                    FILTER(?pGenero IN (dbo:genre, dbp:genres, prop-es:géneros))
                    ?generoURI rdfs:label ?generoName .
                    FILTER(lang(?generoName) = "{language}" || lang(?generoName) = "en")
                }}
                
                ?film ?pSinopsis ?abstract .
                    FILTER(?pSinopsis IN (dbo:abstract, dbo:description))
                    FILTER(lang(?abstract) = "{language}" || lang(?abstract) = "en")
                
                {filter_block}
            }}
            GROUP BY ?film ?title ?releaseDate ?runtime
            LIMIT {limit}
            """
            print ("actor", {actor}, "director", {director}, "genero", {genre}, "año", {year}, "org", {studio})
            return self._run_sparql(query, language)

        except Exception as e:
            logger.error(
                f"Error en búsqueda semántica DBpedia ({language}): {e}", exc_info=True)
            return []

    def _run_sparql(self, query, language='es'):
        """Ejecuta la consulta SPARQL con cache y procesa resultados eficientemente"""
        try:
            cache_key = self._generate_cache_key(query)

            # Revisar cache DBpedia
            if cache_key in self.dbpedia_cache:
                return self.dbpedia_cache[cache_key]

            endpoint = self.endpoints.get(language, self.endpoints['es'])
            response = requests.get(
                endpoint,
                params={"query": query, "format": "json"},
                timeout=self.timeout
            )

            content_type = response.headers.get("Content-Type", "")
            if "application/sparql-results+json" not in content_type:
                print("DBpedia no devolvió JSON. Respuesta:")
                print(response.text[:500])
                return []

            data = response.json()
            results_raw = data.get("results", {}).get("bindings", [])

            results = []

            # Preparar títulos para llamadas paralelas a TMDB
            titles = [b.get("title", {}).get("value") for b in results_raw]

            # Llamadas paralelas a TMDB
            with ThreadPoolExecutor(max_workers=5) as executor:
                tmdb_results = list(
                    executor.map(lambda t: self._fetch_tmdb(t, language), titles)
                )

            for i, b in enumerate(results_raw):
                uri = b.get("film", {}).get("value")
                titulo_dbp = b.get("title", {}).get("value", "Título no disponible")

                # Directores
                directores_str = b.get("directores", {}).get("value", "")
                directores = (
                    [d.strip() for d in directores_str.split(",")]
                    if directores_str else ["Director no disponible"]
                )

                # Actores
                actores_str = b.get("actores", {}).get("value", "")
                actores = (
                    [a.strip() for a in actores_str.split(",")]
                    if actores_str else ["Actores no disponibles"]
                )

                # Géneros
                generos_str = b.get("generos", {}).get("value", "")
                generos = (
                    [g.strip() for g in generos_str.split(",")]
                    if generos_str else ["Géneros no disponibles"]
                )

                # Sinopsis
                abstract = b.get("abstract", {}).get("value", "")
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."

                # Año
                release_date = b.get("releaseDate", {}).get("value", "")
                year = release_date.split("-")[0] if release_date else "No disponible"

                # Duración
                runtime = b.get("runtime", {}).get("value", "")
                if runtime:
                    try:
                        runtime_minutes = int(float(runtime))
                        if runtime_minutes > 1000:
                            runtime_minutes //= 60
                        runtime = f"{runtime_minutes} min"
                    except:
                        runtime = "No disponible"
                else:
                    runtime = "No disponible"

                # TMDB
                tmdb_data = tmdb_results[i] if i < len(tmdb_results) else None
                if tmdb_data:
                    titulo_tmdb = tmdb_data.get("title", titulo_dbp)
                    poster_url = (
                        f"https://image.tmdb.org/t/p/w500{tmdb_data.get('poster_path')}"
                        if tmdb_data.get("poster_path")
                        else None
                    )
                else:
                    titulo_tmdb = titulo_dbp
                    poster_url = None

                results.append({
                    "uri": uri,
                    "titulo": titulo_tmdb,
                    "poster": poster_url,
                    "directores": directores,
                    "actores": actores,
                    "generos": generos,
                    "sinopsis": abstract or "Sinopsis no disponible",
                    "anio": year,
                    "duracion": runtime,
                    "fuente": f"DBpedia ({language.upper()})",
                    "tipo": "external",
                    "idioma": language
                })

            # Guardar en cache DBpedia
            self.dbpedia_cache[cache_key] = results
            return results

        except Exception as e:
            print(f"Error en _run_sparql ({language}): {e}")
            return []

    def search_people_from_movie(self, movie_title, role=None, language="es", limit=50):
        try:
            title_safe = movie_title.replace('"', '\\"')

            # Propiedades de DBpedia según tipo de persona
            role_properties = {
                "actor": ["dbo:starring", "dbo:castMember", "dbp:starring", "dbo:actor"],
                "director": ["dbo:director", "dbp:director"],
                "writer": ["dbo:writer", "dbp:writer", "dbo:screenplay"],
                "producer": ["dbo:producer", "dbp:producer"],
                "character": ["dbo:character", "dbp:characters"]
            }

            # Si no se especificó rol
            all_properties = set()
            for props in role_properties.values():
                all_properties.update(props)

            # Si se especificó un rol
            selected_props = (
                role_properties[role.lower()] if role and role.lower() in role_properties
                else list(all_properties)
            )

            prop_filter = " , ".join(selected_props)

            query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?person ?name ?birthDate ?abstract WHERE {{
                ?film rdf:type dbo:Film .
                ?film rdfs:label ?title .
                FILTER(lang(?title) = "{language}")
                FILTER( regex(lcase(str(?title)), lcase("{title_safe}"), "i") )

                # Relación película -> persona
                ?film ?prop ?person .
                FILTER(?prop IN ({prop_filter}))

                # Datos de la persona
                ?person rdfs:label ?name .
                FILTER(lang(?name) = "{language}" || lang(?name) = "en")

                OPTIONAL {{ ?person dbo:birthDate ?birthDate }}

                OPTIONAL {{
                    ?person dbo:abstract ?abstract .
                    FILTER(lang(?abstract) = "{language}")
                }}
            }}
            LIMIT {limit}
            """

            raw_results = self._run_sparql(query, language)

            people = []
            for b in raw_results:
                people.append({
                    "uri": b.get("uri"),
                    "nombre": b.get("titulo"),
                    "fecha_nacimiento": b.get("anio", "No disponible"),
                    "biografia": b.get("sinopsis", "No disponible"),
                    "fuente": b.get("fuente"),
                    "idioma": language,
                    "tipo": "persona"
                })

            return people

        except Exception as e:
            logger.error(f"Error buscando personas de película: {e}", exc_info=True)
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

    def _generate_cache_key(self, query: str):
        # Hash para usar como key de cache
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def _fetch_tmdb(self, title: str, language: str):
        # Revisar cache primero
        cache_key = f"{title}:{language}"
        if cache_key in self.tmdb_cache:
            return self.tmdb_cache[cache_key]

        # Aquí iría tu lógica real de llamada a TMDB
        tmdb_data = tmdb_service.search_movie_by_title(title, language)

        # Guardar en cache
        self.tmdb_cache[cache_key] = tmdb_data
        return tmdb_data