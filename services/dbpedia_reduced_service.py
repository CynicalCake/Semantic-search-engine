"""
Servicio para manejar una versión reducida de DBpedia con datos específicos de películas.
Este servicio descarga y mantiene un subconjunto de datos de películas de DBpedia
para uso offline.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import time

logger = logging.getLogger(__name__)

class DBpediaReducedService:
    """Servicio para manejar una versión reducida de DBpedia con datos de películas"""
    
    def __init__(self, data_file: str = "dbpedia_reduced.ttl", 
                 metadata_file: str = "dbpedia_reduced_metadata.json"):
        self.data_file = data_file
        self.metadata_file = metadata_file
        self.graph = Graph()
        self.update_interval = timedelta(days=7)  # Actualizar cada semana
        
        # Namespace definitions
        self.dbo = Namespace("http://dbpedia.org/ontology/")
        self.dbr = Namespace("http://dbpedia.org/resource/")
        self.dbp = Namespace("http://dbpedia.org/property/")
        
        # Bind namespaces to the graph
        self.graph.bind("dbo", self.dbo)
        self.graph.bind("dbr", self.dbr)
        self.graph.bind("dbp", self.dbp)
        self.graph.bind("rdfs", RDFS)
        
        self.endpoints = {
            'es': 'http://es.dbpedia.org/sparql',
            'en': 'http://dbpedia.org/sparql',
            'fr': 'http://fr.dbpedia.org/sparql',
            'de': 'http://de.dbpedia.org/sparql'
        }
        
        # Configuración de descarga por categorías
        self.download_strategy = {
            'recent_movies': 1000,     # Películas recientes (2000-2025)
            'classic_movies': 800,     # Películas clásicas (1980-1999)
            'popular_directors': 600,  # Películas de directores conocidos
            'award_winners': 400       # Películas premiadas
        }
        
        self._load_or_initialize()
    
    def _load_or_initialize(self):
        """Carga datos existentes o inicializa la descarga"""
        if os.path.exists(self.data_file) and os.path.exists(self.metadata_file):
            try:
                # Cargar datos existentes
                self.graph.parse(self.data_file, format="turtle")
                logger.info(f"Cargados {len(self.graph)} triples desde {self.data_file}")
                
                # Verificar si necesita actualización
                if self._needs_update():
                    logger.info("Los datos necesitan actualización, iniciando descarga...")
                    self._download_movie_data()
                else:
                    logger.info("Datos de DBpedia reducida están actualizados")
                    
            except Exception as e:
                logger.error(f"Error cargando datos existentes: {e}")
                logger.info("Iniciando descarga completa...")
                self._download_movie_data()
        else:
            logger.info("No se encontraron datos existentes, iniciando descarga...")
            self._download_movie_data()
    
    def _needs_update(self) -> bool:
        """Verifica si los datos necesitan actualización"""
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                last_update = datetime.fromisoformat(metadata.get('last_update', '2000-01-01'))
                return datetime.now() - last_update > self.update_interval
        except:
            return True
    
    def _download_movie_data(self):
        """Descarga datos de películas de DBpedia usando método simple y robusto"""
        logger.info("Iniciando descarga de datos de películas desde DBpedia...")
        
        # Limpiar datos existentes
        self.graph = Graph()
        self.graph.bind("dbo", self.dbo)
        self.graph.bind("dbr", self.dbr)
        self.graph.bind("dbp", self.dbp)
        self.graph.bind("rdfs", RDFS)
        
        total_movies = 0
        
        # Usar método simple que funciona
        for language in ['en', 'es']:
            try:
                logger.info(f"Descargando películas desde DBpedia {language.upper()}...")
                count = self._download_from_endpoint(language, 1000)  # 1000 por idioma
                total_movies += count
                logger.info(f"Descargadas {count} películas desde {language.upper()}")
                time.sleep(3)  # Pausa entre endpoints
            except Exception as e:
                logger.error(f"Error descargando desde {language}: {e}")
        
        # Guardar datos y metadata
        self._save_data(total_movies)
        logger.info(f"Descarga completa: {total_movies} películas en total, {len(self.graph)} triples")
    
    def _download_from_endpoint(self, language: str, limit: int = 2000) -> int:
        """Descarga datos desde un endpoint específico"""
        endpoint = self.endpoints.get(language)
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(60)  # Aumentar timeout
        
        # Query simplificada sin filtros problemáticos de fecha
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?movie ?title ?director ?directorName ?abstract ?releaseDate ?runtime
        WHERE {{
            ?movie a dbo:Film ;
                   rdfs:label ?title ;
                   dbo:director ?director .
            
            ?director rdfs:label ?directorName .
            FILTER(lang(?directorName) = "{language}" || lang(?directorName) = "en")
            
            OPTIONAL {{ 
                ?movie dbo:abstract ?abstract . 
                FILTER(lang(?abstract) = "{language}")
            }}
            
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate }}
            OPTIONAL {{ ?movie dbo:runtime ?runtime }}
            
            FILTER(lang(?title) = "{language}")
        }}
        ORDER BY ?title
        LIMIT {limit}
        """
        
        return self._execute_simple_query(sparql, query, language)
        
        sparql.setQuery(query)
        results = sparql.query().convert()
        
        movies_count = 0
        processed_movies = set()
        
        for binding in results["results"]["bindings"]:
            try:
                movie_uri = URIRef(binding["movie"]["value"])
                
                # Evitar duplicados
                if str(movie_uri) in processed_movies:
                    continue
                processed_movies.add(str(movie_uri))
                
                # Usar el método simplificado
                movies_count += self._process_movie_data(movie_uri, binding, language)
                
            except Exception as e:
                logger.error(f"Error procesando película: {e}")
                continue
        
        return movies_count
    
    def _process_movie_data(self, movie_uri: URIRef, binding: dict, language: str) -> int:
        """Procesa y guarda los datos de una película"""
        try:
            # Agregar tipo de película
            self.graph.add((movie_uri, RDF.type, self.dbo.Film))
            
            # Título
            if "title" in binding:
                title = Literal(binding["title"]["value"], lang=language)
                self.graph.add((movie_uri, RDFS.label, title))
            
            # Director
            if "director" in binding and "directorName" in binding:
                director_uri = URIRef(binding["director"]["value"])
                director_name = Literal(binding["directorName"]["value"])
                self.graph.add((movie_uri, self.dbo.director, director_uri))
                self.graph.add((director_uri, RDFS.label, director_name))
            
            # Abstract/Sinopsis
            if "abstract" in binding:
                abstract = Literal(binding["abstract"]["value"], lang=language)
                self.graph.add((movie_uri, self.dbo.abstract, abstract))
            
            # Fecha de estreno
            if "releaseDate" in binding:
                release_date = binding["releaseDate"]["value"]
                try:
                    if "T" in release_date:
                        release_date = release_date.split("T")[0]
                    date_literal = Literal(release_date, datatype=XSD.date)
                    self.graph.add((movie_uri, self.dbo.releaseDate, date_literal))
                except:
                    date_literal = Literal(release_date)
                    self.graph.add((movie_uri, self.dbo.releaseDate, date_literal))
            
            # Duración
            if "runtime" in binding:
                try:
                    runtime = float(binding["runtime"]["value"])
                    runtime_literal = Literal(runtime, datatype=XSD.double)
                    self.graph.add((movie_uri, self.dbo.runtime, runtime_literal))
                except:
                    runtime_literal = Literal(binding["runtime"]["value"])
                    self.graph.add((movie_uri, self.dbo.runtime, runtime_literal))
            
            return 1  # Película procesada exitosamente
            
        except Exception as e:
            logger.error(f"Error procesando datos de película: {e}")
            return 0
    
    def _download_recent_movies(self, language: str, limit: int = 1000) -> int:
        """Descarga películas recientes (2000-2025)"""
        return self._download_with_query(language, "recent", limit, 2000, 2025)
    
    def _download_classic_movies(self, language: str, limit: int = 800) -> int:
        """Descarga películas clásicas (1980-1999)"""
        return self._download_with_query(language, "classic", limit, 1980, 1999)
    
    def _download_popular_directors_movies(self, language: str, limit: int = 600) -> int:
        """Descarga películas de directores populares"""
        directors = [
            "Steven Spielberg", "Martin Scorsese", "Christopher Nolan",
            "Quentin Tarantino", "Alfred Hitchcock", "Stanley Kubrick",
            "Francis Ford Coppola", "Ridley Scott", "James Cameron",
            "Tim Burton", "David Fincher", "Denis Villeneuve",
            "Alejandro González Iñárritu", "Alfonso Cuarón", "Guillermo del Toro"
        ]
        
        total_count = 0
        movies_per_director = min(50, limit // len(directors))
        
        for director in directors:
            if total_count >= limit:
                break
            count = self._download_director_movies(language, director, movies_per_director)
            total_count += count
            time.sleep(1)  # Pausa entre directores
            
        return total_count
    
    def _download_with_query(self, language: str, category: str, limit: int, 
                           year_start: int = None, year_end: int = None) -> int:
        """Descarga películas con query específica por categoría"""
        endpoint = self.endpoints.get(language)
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(60)
        
        # Construir filtro de años
        year_filter = ""
        if year_start and year_end:
            year_filter = f"FILTER(BOUND(?releaseDate) && YEAR(?releaseDate) >= {year_start} && YEAR(?releaseDate) <= {year_end})"
        
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?movie ?title ?director ?directorName ?abstract ?releaseDate 
                       ?runtime ?genre ?genreName ?country ?countryName
        WHERE {{
            ?movie a dbo:Film ;
                   rdfs:label ?title ;
                   dbo:director ?director .
            
            ?director rdfs:label ?directorName .
            FILTER(lang(?directorName) = "{language}" || lang(?directorName) = "en")
            
            OPTIONAL {{ 
                ?movie dbo:abstract ?abstract . 
                FILTER(lang(?abstract) = "{language}")
            }}
            
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate }}
            OPTIONAL {{ ?movie dbo:runtime ?runtime }}
            
            OPTIONAL {{ 
                ?movie dbo:genre ?genre .
                ?genre rdfs:label ?genreName .
                FILTER(lang(?genreName) = "{language}" || lang(?genreName) = "en")
            }}
            
            OPTIONAL {{
                ?movie dbo:country ?country .
                ?country rdfs:label ?countryName .
                FILTER(lang(?countryName) = "{language}" || lang(?countryName) = "en")
            }}
            
            FILTER(lang(?title) = "{language}")
            {year_filter}
        }}
        ORDER BY DESC(?releaseDate) ?title
        LIMIT {limit}
        """
        
        return self._execute_query_and_save(sparql, query, language, category)
    
    def _download_director_movies(self, language: str, director_name: str, limit: int = 50) -> int:
        """Descarga películas de un director específico"""
        endpoint = self.endpoints.get(language)
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(60)
        
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?movie ?title ?director ?directorName ?abstract ?releaseDate 
                       ?runtime ?genre ?genreName ?country ?countryName
        WHERE {{
            ?movie a dbo:Film ;
                   rdfs:label ?title ;
                   dbo:director ?director .
            
            ?director rdfs:label ?directorName .
            
            OPTIONAL {{ 
                ?movie dbo:abstract ?abstract . 
                FILTER(lang(?abstract) = "{language}")
            }}
            
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate }}
            OPTIONAL {{ ?movie dbo:runtime ?runtime }}
            
            OPTIONAL {{ 
                ?movie dbo:genre ?genre .
                ?genre rdfs:label ?genreName .
                FILTER(lang(?genreName) = "{language}" || lang(?genreName) = "en")
            }}
            
            OPTIONAL {{
                ?movie dbo:country ?country .
                ?country rdfs:label ?countryName .
                FILTER(lang(?countryName) = "{language}" || lang(?countryName) = "en")
            }}
            
            FILTER(lang(?title) = "{language}")
            FILTER regex(?directorName, "{director_name}", "i")
        }}
        ORDER BY DESC(?releaseDate)
        LIMIT {limit}
        """
        
        return self._execute_query_and_save(sparql, query, language, f"director_{director_name}")
    
    def _execute_query_and_save(self, sparql, query: str, language: str, category: str) -> int:
        """Ejecuta query y guarda los resultados en el grafo"""
        try:
            sparql.setQuery(query)
            results = sparql.query().convert()
            
            movies_count = 0
            processed_movies = getattr(self, '_processed_movies', set())
            
            for binding in results["results"]["bindings"]:
                try:
                    movie_uri = URIRef(binding["movie"]["value"])
                    
                    # Evitar duplicados globales
                    if str(movie_uri) in processed_movies:
                        continue
                    processed_movies.add(str(movie_uri))
                    
                    # Procesar igual que en el método original
                    self.graph.add((movie_uri, RDF.type, self.dbo.Film))
                    
                    # Título
                    if "title" in binding:
                        title = Literal(binding["title"]["value"], lang=language)
                        self.graph.add((movie_uri, RDFS.label, title))
                    
                    # Director
                    if "director" in binding and "directorName" in binding:
                        director_uri = URIRef(binding["director"]["value"])
                        director_name = Literal(binding["directorName"]["value"])
                        self.graph.add((movie_uri, self.dbo.director, director_uri))
                        self.graph.add((director_uri, RDFS.label, director_name))
                    
                    # Abstract/Sinopsis
                    if "abstract" in binding:
                        abstract = Literal(binding["abstract"]["value"], lang=language)
                        self.graph.add((movie_uri, self.dbo.abstract, abstract))
                    
                    # Fecha de estreno
                    if "releaseDate" in binding:
                        release_date = binding["releaseDate"]["value"]
                        try:
                            if "T" in release_date:
                                release_date = release_date.split("T")[0]
                            date_literal = Literal(release_date, datatype=XSD.date)
                            self.graph.add((movie_uri, self.dbo.releaseDate, date_literal))
                        except:
                            date_literal = Literal(release_date)
                            self.graph.add((movie_uri, self.dbo.releaseDate, date_literal))
                    
                    # Duración
                    if "runtime" in binding:
                        try:
                            runtime = float(binding["runtime"]["value"])
                            runtime_literal = Literal(runtime, datatype=XSD.double)
                            self.graph.add((movie_uri, self.dbo.runtime, runtime_literal))
                        except:
                            runtime_literal = Literal(binding["runtime"]["value"])
                            self.graph.add((movie_uri, self.dbo.runtime, runtime_literal))
                    
                    # Género
                    if "genre" in binding and "genreName" in binding:
                        genre_uri = URIRef(binding["genre"]["value"])
                        genre_name = Literal(binding["genreName"]["value"])
                        self.graph.add((movie_uri, self.dbo.genre, genre_uri))
                        self.graph.add((genre_uri, RDFS.label, genre_name))
                    
                    # País
                    if "country" in binding and "countryName" in binding:
                        country_uri = URIRef(binding["country"]["value"])
                        country_name = Literal(binding["countryName"]["value"])
                        self.graph.add((movie_uri, self.dbo.country, country_uri))
                        self.graph.add((country_uri, RDFS.label, country_name))
                    
                    movies_count += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando película: {e}")
                    continue
            
            # Guardar el conjunto de películas procesadas para evitar duplicados globales
            self._processed_movies = processed_movies
            
            logger.debug(f"Categoría {category} ({language}): {movies_count} películas")
            return movies_count
            
        except Exception as e:
            logger.error(f"Error ejecutando query para {category}: {e}")
            return 0
    
    def _save_data(self, movie_count: int):
        """Guarda los datos descargados y metadata"""
        try:
            # Guardar grafo en formato Turtle
            self.graph.serialize(destination=self.data_file, format="turtle")
            
            # Guardar metadata
            metadata = {
                "last_update": datetime.now().isoformat(),
                "movie_count": movie_count,
                "triple_count": len(self.graph),
                "version": "1.0"
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Datos guardados: {movie_count} películas, {len(self.graph)} triples")
            
        except Exception as e:
            logger.error(f"Error guardando datos: {e}")
            raise
    
    def search_movies(self, term: str, limit: int = 20) -> List[Dict]:
        """Busca películas en la DBpedia reducida"""
        if len(self.graph) == 0:
            logger.warning("DBpedia reducida no tiene datos disponibles")
            return []
        
        movies = []
        
        # Query SPARQL para buscar películas
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?movie ?title ?director ?directorName ?abstract ?releaseDate ?runtime ?genre ?genreName ?country ?countryName
        WHERE {{
            ?movie a dbo:Film ;
                   rdfs:label ?title .
                   
            OPTIONAL {{ 
                ?movie dbo:director ?director . 
                ?director rdfs:label ?directorName .
            }}
            
            OPTIONAL {{ ?movie dbo:abstract ?abstract }}
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate }}
            OPTIONAL {{ ?movie dbo:runtime ?runtime }}
            
            OPTIONAL {{ 
                ?movie dbo:genre ?genre .
                ?genre rdfs:label ?genreName .
            }}
            
            OPTIONAL {{
                ?movie dbo:country ?country .
                ?country rdfs:label ?countryName .
            }}
            
            FILTER regex(?title, "{term.replace('"', '')}", "i")
        }}
        ORDER BY ?title
        LIMIT {limit}
        """
        
        try:
            results = list(self.graph.query(query))
            
            for row in results:
                # Procesar fecha
                release_date = str(row[5]) if row[5] else ""
                year = "No disponible"
                if release_date:
                    try:
                        if "T" in release_date:
                            year = release_date.split("-")[0]
                        elif "-" in release_date:
                            year = release_date.split("-")[0]
                        else:
                            year = release_date[:4] if len(release_date) >= 4 else release_date
                    except:
                        year = "No disponible"
                
                # Procesar duración
                runtime = str(row[6]) if row[6] else ""
                duration = "No disponible"
                if runtime:
                    try:
                        runtime_minutes = int(float(runtime))
                        if runtime_minutes > 1000:
                            runtime_minutes = runtime_minutes // 60
                        duration = f"{runtime_minutes} min"
                    except:
                        duration = "No disponible"
                
                # Procesar sinopsis
                abstract = str(row[4]) if row[4] else "Sinopsis no disponible"
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."
                
                movie = {
                    "titulo": str(row[1]) if row[1] else "Título no disponible",
                    "director": str(row[3]) if row[3] else "Director no disponible",
                    "sinopsis": abstract,
                    "anio": year,
                    "duracion": duration,
                    "genero": str(row[8]) if row[8] else "No disponible",
                    "pais": str(row[10]) if row[10] else "No disponible",
                    "uri": str(row[0]) if row[0] else "",
                    "fuente": "DBpedia Reducida (Offline)",
                    "tipo": "reduced",
                    "origen": "dbpedia_local"
                }
                movies.append(movie)
                
            logger.info(f"Encontradas {len(movies)} películas en DBpedia reducida para '{term}'")
            return movies
            
        except Exception as e:
            logger.error(f"Error en búsqueda de DBpedia reducida: {e}")
            return []
    
    def search_movies_semantic(self, actor: str = None, director: str = None, 
                             year: str = None, genre: str = None) -> List[Dict]:
        """Búsqueda semántica en DBpedia reducida"""
        if len(self.graph) == 0:
            return []
        
        # Construir query dinámicamente
        filters = []
        if actor:
            # Nota: En esta versión simplificada, no incluimos actores
            # Se podría expandir en el futuro
            pass
        if director:
            filters.append(f'FILTER regex(?directorName, "{director.replace('"', '')}", "i")')
        if year:
            filters.append(f'FILTER regex(str(?releaseDate), "{year}", "i")')
        if genre:
            filters.append(f'FILTER regex(?genreName, "{genre.replace('"', '')}", "i")')
        
        filter_clause = " ".join(filters) if filters else ""
        
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?movie ?title ?director ?directorName ?abstract ?releaseDate ?runtime ?genre ?genreName ?country ?countryName
        WHERE {{
            ?movie a dbo:Film ;
                   rdfs:label ?title .
                   
            OPTIONAL {{ 
                ?movie dbo:director ?director . 
                ?director rdfs:label ?directorName .
            }}
            
            OPTIONAL {{ ?movie dbo:abstract ?abstract }}
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate }}
            OPTIONAL {{ ?movie dbo:runtime ?runtime }}
            
            OPTIONAL {{ 
                ?movie dbo:genre ?genre .
                ?genre rdfs:label ?genreName .
            }}
            
            OPTIONAL {{
                ?movie dbo:country ?country .
                ?country rdfs:label ?countryName .
            }}
            
            {filter_clause}
        }}
        ORDER BY ?title
        LIMIT 20
        """
        
        try:
            results = list(self.graph.query(query))
            movies = []
            
            for row in results:
                # Usar la misma lógica de procesamiento que search_movies
                release_date = str(row[5]) if row[5] else ""
                year_parsed = "No disponible"
                if release_date:
                    try:
                        year_parsed = release_date.split("-")[0] if "-" in release_date else release_date[:4]
                    except:
                        pass
                
                runtime = str(row[6]) if row[6] else ""
                duration = "No disponible"
                if runtime:
                    try:
                        runtime_minutes = int(float(runtime))
                        if runtime_minutes > 1000:
                            runtime_minutes = runtime_minutes // 60
                        duration = f"{runtime_minutes} min"
                    except:
                        pass
                
                abstract = str(row[4]) if row[4] else "Sinopsis no disponible"
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."
                
                movie = {
                    "titulo": str(row[1]) if row[1] else "Título no disponible",
                    "director": str(row[3]) if row[3] else "Director no disponible",
                    "sinopsis": abstract,
                    "anio": year_parsed,
                    "duracion": duration,
                    "genero": str(row[8]) if row[8] else "No disponible",
                    "pais": str(row[10]) if row[10] else "No disponible",
                    "uri": str(row[0]) if row[0] else "",
                    "fuente": "DBpedia Reducida (Offline)",
                    "tipo": "reduced",
                    "origen": "dbpedia_local"
                }
                movies.append(movie)
            
            return movies
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica de DBpedia reducida: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de la DBpedia reducida"""
        try:
            movie_count = 0
            director_count = 0
            genre_count = 0
            
            # Contar películas
            movie_query = """
            PREFIX dbo: <http://dbpedia.org/ontology/>
            SELECT (COUNT(DISTINCT ?movie) AS ?count)
            WHERE { ?movie a dbo:Film }
            """
            results = list(self.graph.query(movie_query))
            if results:
                movie_count = int(results[0][0])
            
            # Contar directores
            director_query = """
            PREFIX dbo: <http://dbpedia.org/ontology/>
            SELECT (COUNT(DISTINCT ?director) AS ?count)
            WHERE { ?movie dbo:director ?director }
            """
            results = list(self.graph.query(director_query))
            if results:
                director_count = int(results[0][0])
            
            # Contar géneros
            genre_query = """
            PREFIX dbo: <http://dbpedia.org/ontology/>
            SELECT (COUNT(DISTINCT ?genre) AS ?count)
            WHERE { ?movie dbo:genre ?genre }
            """
            results = list(self.graph.query(genre_query))
            if results:
                genre_count = int(results[0][0])
            
            # Cargar metadata si existe
            metadata = {}
            if os.path.exists(self.metadata_file):
                try:
                    with open(self.metadata_file, 'r') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            return {
                "peliculas": movie_count,
                "directores": director_count,
                "generos": genre_count,
                "triples_total": len(self.graph),
                "ultima_actualizacion": metadata.get('last_update', 'Desconocida'),
                "version": metadata.get('version', '1.0')
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                "peliculas": 0,
                "directores": 0,
                "generos": 0,
                "triples_total": len(self.graph),
                "ultima_actualizacion": "Error",
                "version": "1.0"
            }
    
    def force_update(self):
        """Fuerza una actualización de los datos"""
        logger.info("Forzando actualización de DBpedia reducida...")
        self._download_movie_data()
    
    def expand_database(self, additional_movies: int = 1000):
        """Expande la base de datos con más películas usando método robusto"""
        logger.info(f"Expandiendo base de datos con {additional_movies} películas adicionales...")
        
        current_size = len(self.graph)
        current_movies = self.get_movie_count()
        
        # Usar el método original que ya funciona, pero con límites más altos
        total_added = 0
        
        # Estrategia 1: Más películas en inglés (más contenido disponible)
        try:
            logger.info("Descargando películas adicionales desde DBpedia EN...")
            count_en = self._download_from_endpoint_enhanced("en", additional_movies // 2)
            total_added += count_en
            logger.info(f"Agregadas {count_en} películas desde EN")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error descargando desde EN: {e}")
        
        # Estrategia 2: Más películas en español
        if total_added < additional_movies:
            remaining = additional_movies - total_added
            try:
                logger.info("Descargando películas adicionales desde DBpedia ES...")
                count_es = self._download_from_endpoint_enhanced("es", remaining)
                total_added += count_es
                logger.info(f"Agregadas {count_es} películas desde ES")
                time.sleep(3)
            except Exception as e:
                logger.error(f"Error descargando desde ES: {e}")
        
        # Guardar datos actualizados
        final_movie_count = self.get_movie_count()
        self._save_data(final_movie_count)
        
        new_size = len(self.graph)
        logger.info(f"Base expandida: {current_size} -> {new_size} triples")
        logger.info(f"Películas: {current_movies} -> {final_movie_count}")
        
        return final_movie_count - current_movies
    
    def _download_from_endpoint_enhanced(self, language: str, limit: int = 500) -> int:
        """Versión mejorada del método original que funciona"""
        endpoint = self.endpoints.get(language)
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(60)
        
        # Query más simple y robusta
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?movie ?title ?director ?directorName ?abstract ?releaseDate ?runtime
        WHERE {{
            ?movie a dbo:Film ;
                   rdfs:label ?title .
            
            OPTIONAL {{ 
                ?movie dbo:director ?director . 
                ?director rdfs:label ?directorName .
                FILTER(lang(?directorName) = "{language}" || lang(?directorName) = "en")
            }}
            
            OPTIONAL {{ 
                ?movie dbo:abstract ?abstract . 
                FILTER(lang(?abstract) = "{language}")
            }}
            
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate }}
            OPTIONAL {{ ?movie dbo:runtime ?runtime }}
            
            FILTER(lang(?title) = "{language}")
            FILTER(BOUND(?director))
        }}
        ORDER BY ?title
        LIMIT {limit}
        """
        
        return self._execute_simple_query(sparql, query, language)
    
    def _execute_simple_query(self, sparql, query: str, language: str) -> int:
        """Ejecuta una query simple y guarda resultados"""
        try:
            sparql.setQuery(query)
            results = sparql.query().convert()
            
            movies_count = 0
            processed_movies = getattr(self, '_processed_movies', set())
            
            for binding in results["results"]["bindings"]:
                try:
                    movie_uri = URIRef(binding["movie"]["value"])
                    
                    # Evitar duplicados
                    if str(movie_uri) in processed_movies:
                        continue
                    processed_movies.add(str(movie_uri))
                    
                    # Agregar tipo de película
                    self.graph.add((movie_uri, RDF.type, self.dbo.Film))
                    
                    # Título
                    if "title" in binding:
                        title = Literal(binding["title"]["value"], lang=language)
                        self.graph.add((movie_uri, RDFS.label, title))
                    
                    # Director
                    if "director" in binding and "directorName" in binding:
                        director_uri = URIRef(binding["director"]["value"])
                        director_name = Literal(binding["directorName"]["value"])
                        self.graph.add((movie_uri, self.dbo.director, director_uri))
                        self.graph.add((director_uri, RDFS.label, director_name))
                    
                    # Abstract/Sinopsis
                    if "abstract" in binding:
                        abstract = Literal(binding["abstract"]["value"], lang=language)
                        self.graph.add((movie_uri, self.dbo.abstract, abstract))
                    
                    # Fecha de estreno
                    if "releaseDate" in binding:
                        release_date = binding["releaseDate"]["value"]
                        try:
                            if "T" in release_date:
                                release_date = release_date.split("T")[0]
                            date_literal = Literal(release_date, datatype=XSD.date)
                            self.graph.add((movie_uri, self.dbo.releaseDate, date_literal))
                        except:
                            date_literal = Literal(release_date)
                            self.graph.add((movie_uri, self.dbo.releaseDate, date_literal))
                    
                    # Duración
                    if "runtime" in binding:
                        try:
                            runtime = float(binding["runtime"]["value"])
                            runtime_literal = Literal(runtime, datatype=XSD.double)
                            self.graph.add((movie_uri, self.dbo.runtime, runtime_literal))
                        except:
                            runtime_literal = Literal(binding["runtime"]["value"])
                            self.graph.add((movie_uri, self.dbo.runtime, runtime_literal))
                    
                    movies_count += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando película: {e}")
                    continue
            
            # Guardar conjunto para evitar duplicados
            self._processed_movies = processed_movies
            
            return movies_count
            
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            return 0
    
    def _download_by_genre(self, language: str, genre: str, limit: int = 100) -> int:
        """Descarga películas por género específico"""
        endpoint = self.endpoints.get(language)
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(60)
        
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?movie ?title ?director ?directorName ?abstract ?releaseDate 
                       ?runtime ?genre ?genreName ?country ?countryName
        WHERE {{
            ?movie a dbo:Film ;
                   rdfs:label ?title ;
                   dbo:genre ?genre ;
                   dbo:director ?director .
            
            ?genre rdfs:label ?genreName .
            ?director rdfs:label ?directorName .
            
            FILTER regex(?genreName, "{genre}", "i")
            FILTER(lang(?title) = "{language}")
            FILTER(lang(?directorName) = "{language}" || lang(?directorName) = "en")
            
            OPTIONAL {{ 
                ?movie dbo:abstract ?abstract . 
                FILTER(lang(?abstract) = "{language}")
            }}
            
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate }}
            OPTIONAL {{ ?movie dbo:runtime ?runtime }}
            
            OPTIONAL {{
                ?movie dbo:country ?country .
                ?country rdfs:label ?countryName .
                FILTER(lang(?countryName) = "{language}" || lang(?countryName) = "en")
            }}
        }}
        ORDER BY DESC(?releaseDate) ?title
        LIMIT {limit}
        """
        
        return self._execute_query_and_save(sparql, query, language, f"genre_{genre}")
    
    def get_movie_count(self) -> int:
        """Obtiene el número actual de películas en la base"""
        query = """
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT (COUNT(DISTINCT ?movie) AS ?count)
        WHERE { ?movie a dbo:Film }
        """
        
        try:
            results = list(self.graph.query(query))
            return int(results[0][0]) if results else 0
        except:
            return 0
    
    def get_recommended_size(self) -> dict:
        """Recomienda tamaños de base de datos según uso"""
        return {
            "pequeña": {
                "movies": 500,
                "description": "Para pruebas y desarrollo rápido"
            },
            "mediana": {
                "movies": 2000,
                "description": "Para uso académico y demostraciones"
            },
            "grande": {
                "movies": 5000,
                "description": "Para aplicaciones de producción"
            },
            "completa": {
                "movies": 10000,
                "description": "Base de datos extensa para investigación"
            }
        }
    
    def health_check(self) -> bool:
        """Verifica el estado del servicio"""
        return len(self.graph) > 0