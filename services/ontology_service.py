from rdflib import Graph, Namespace
import logging
import os
import time
from typing import List, Dict, Optional
from services.mapping import PROPERTY_MAPPING, RELATION_MAPPING, LOCAL_NS

logger = logging.getLogger(__name__)

class OntologyService:
    """Servicio para manejar consultas a la ontología local"""
    
    def __init__(self, ontology_file: str):
        self.ontology_file = ontology_file
        self.ontology_path = ontology_file
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
            
        movies = []
        movie_count = 0
        
        try:
            # Búsqueda directa en los triples, más robusta que SPARQL complejo
            for subject, predicate, obj in self.graph:
                if movie_count >= limit:
                    break
                    
                # Buscar triples que contengan nombrePelicula
                if 'nombrePelicula' in str(predicate):
                    title = str(obj)
                    
                    # Verificar si el término está en el título (búsqueda case-insensitive)
                    if term.lower() in title.lower():
                        # Obtener URI de la película
                        movie_uri = str(subject)
                        
                        # Buscar información adicional de esta película
                        director = "No disponible"
                        year = "No disponible"
                        pais = "No disponible"
                        genero = "No disponible"
                        
                        # Buscar toda la información relacionada con esta película
                        for s2, p2, o2 in self.graph:
                            if str(s2) == movie_uri:
                                predicate_str = str(p2)
                                
                                if 'dirigidaPor' in predicate_str:
                                    # Buscar nombre del director
                                    director_uri = str(o2)
                                    for s3, p3, o3 in self.graph:
                                        if str(s3) == director_uri and 'nombrePersona' in str(p3):
                                            director = str(o3)
                                            break
                                elif 'anioEstreno' in predicate_str:
                                    year = str(o2)
                                elif 'paisPelicula' in predicate_str:
                                    pais = str(o2)
                                elif 'tieneGenero' in predicate_str:
                                    # Buscar nombre del género
                                    genero_uri = str(o2)
                                    for s3, p3, o3 in self.graph:
                                        if str(s3) == genero_uri and 'nombreGenero' in str(p3):
                                            genero = str(o3)
                                            break
                                    # Si no se encontró nombreGenero, usar la URI como fallback
                                    if genero == "No disponible":
                                        genero_name = genero_uri.split('#')[-1] if '#' in genero_uri else str(o2)
                                        genero = genero_name
                        
                        movie = {
                            "titulo": title,
                            "director": director,
                            "anio": year,
                            "genero": genero,
                            "pais": pais,
                            "fuente": "Ontología Local",
                            "tipo": "local",
                            "uri": movie_uri
                        }
                        movies.append(movie)
                        movie_count += 1
            
            logger.info(f"Búsqueda directa encontró {len(movies)} películas para '{term}'")
            return movies
            
        except Exception as e:
            logger.error(f"Error en búsqueda directa para '{term}': {e}")
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
            
            # Usar consultas muy simples para evitar problemas de lambda
            total_triples = len(self.graph)
            
            # Contar películas de manera simple
            movies_count = 0
            directors_count = 0
            
            try:
                # Consulta muy simple para películas
                for s, p, o in self.graph:
                    if 'Pelicula' in str(s) and 'nombrePelicula' in str(p):
                        movies_count += 1
                    if 'dirigidaPor' in str(p):
                        directors_count += 1
                        
                # Limitar a números razonables
                directors_count = min(directors_count, movies_count)
                
            except Exception as count_error:
                logger.warning(f"Error en conteo simple: {count_error}")
                # Si falla, usar heurísticas basadas en triples
                movies_count = total_triples // 10 if total_triples > 0 else 0
                directors_count = movies_count // 2 if movies_count > 0 else 0
            
            return {
                "total_triples": total_triples,
                "total_peliculas": movies_count,
                "total_directores": directors_count,
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
    
    def get_debug_info(self) -> Dict:
        """Obtiene información detallada para debug del archivo OWX"""
        debug_data = {
            'file_info': {},
            'content_analysis': {},
            'loading_attempts': [],
            'graph_content': {},
            'recommendations': []
        }
        
        try:
            # Información del archivo
            if os.path.exists(self.ontology_file):
                stat = os.stat(self.ontology_file)
                debug_data['file_info'] = {
                    'path': self.ontology_file,
                    'exists': True,
                    'size_bytes': stat.st_size,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'last_modified': time.ctime(stat.st_mtime),
                    'extension': os.path.splitext(self.ontology_file)[1]
                }
                
                # Leer primeras líneas del archivo
                with open(self.ontology_file, 'r', encoding='utf-8', errors='ignore') as f:
                    first_lines = []
                    for i, line in enumerate(f):
                        if i >= 25:  # Solo las primeras 25 líneas
                            break
                        first_lines.append(f"{i+1:2d}: {line.rstrip()}")
                    debug_data['content_analysis']['first_lines'] = first_lines
                
                # Detectar formato aparente
                with open(self.ontology_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)  # Primeros 2000 caracteres
                    
                format_indicators = {
                    'XML/OWL': any(indicator in content.lower() for indicator in ['<?xml', '<owl:', 'xmlns:', '<rdf:']),
                    'Turtle': any(indicator in content for indicator in ['@prefix', '@base', '.']),
                    'N-Triples': '<' in content and '>' in content and ' .' in content,
                    'JSON-LD': content.strip().startswith('{') or content.strip().startswith('['),
                    'OWX_Protégé': 'owx' in self.ontology_file.lower(),
                    'Contains_Ontology_Data': any(term in content.lower() for term in ['ontology', 'class', 'property', 'pelicula', 'movie'])
                }
                
                debug_data['content_analysis']['detected_formats'] = {
                    k: v for k, v in format_indicators.items() if v
                }
                
                # Estadísticas del contenido
                lines = content.split('\n')
                debug_data['content_analysis']['stats'] = {
                    'total_characters': len(content),
                    'total_lines_sampled': len(lines),
                    'empty_lines': sum(1 for line in lines if line.strip() == ''),
                    'xml_tags_count': content.count('<'),
                    'contains_spanish': any(word in content.lower() for word in ['película', 'director', 'año', 'género'])
                }
            else:
                debug_data['file_info'] = {
                    'path': self.ontology_file,
                    'exists': False,
                    'error': 'Archivo no encontrado'
                }
                
            # Intentar cargar con diferentes formatos
            formats_to_try = ['xml', 'turtle', 'n3', 'nt', 'json-ld']
            
            for fmt in formats_to_try:
                attempt = {
                    'format': fmt,
                    'success': False,
                    'error': None,
                    'triples_loaded': 0,
                    'execution_time_ms': 0
                }
                
                try:
                    start_time = time.time()
                    test_graph = Graph()
                    test_graph.parse(self.ontology_file, format=fmt)
                    end_time = time.time()
                    
                    attempt['success'] = True
                    attempt['triples_loaded'] = len(test_graph)
                    attempt['execution_time_ms'] = round((end_time - start_time) * 1000, 2)
                    
                    # Si este formato funcionó y tiene datos, analizar contenido
                    if len(test_graph) > 0:
                        debug_data['graph_content'] = self._analyze_graph_content(test_graph)
                        
                except Exception as e:
                    attempt['error'] = str(e)[:200] + '...' if len(str(e)) > 200 else str(e)
                    
                debug_data['loading_attempts'].append(attempt)
            
            # Estado actual del grafo
            debug_data['current_graph'] = {
                'loaded': self.graph is not None,
                'triples': len(self.graph) if self.graph else 0,
                'namespaces': [{'prefix': prefix, 'uri': str(uri)} for prefix, uri in self.graph.namespaces()] if self.graph else []
            }
            
            # Recomendaciones basadas en resultados
            successful_formats = [a for a in debug_data['loading_attempts'] if a['success']]
            if successful_formats:
                best_format = max(successful_formats, key=lambda x: x['triples_loaded'])
                debug_data['recommendations'].append(f"✅ El archivo se puede cargar como {best_format['format']} con {best_format['triples_loaded']} triples")
                if best_format['format'] != 'xml':
                    debug_data['recommendations'].append(f"💡 Considera guardar/exportar la ontología como {best_format['format']} para mejor compatibilidad")
            else:
                debug_data['recommendations'].append("❌ No se pudo cargar el archivo en ningún formato RDF estándar")
                debug_data['recommendations'].append("🔧 Posibles soluciones:")
                debug_data['recommendations'].append("   • Verificar que el archivo sea una ontología válida")
                debug_data['recommendations'].append("   • Si es de Protégé, exportar como OWL/XML o Turtle")
                debug_data['recommendations'].append("   • Verificar la codificación del archivo (debe ser UTF-8)")
                
        except Exception as e:
            debug_data['error'] = str(e)
            logger.error(f"Error en get_debug_info: {e}")
            
        return debug_data
    
    def _analyze_graph_content(self, graph) -> Dict:
        """Analiza el contenido de un grafo RDF cargado exitosamente"""
        analysis = {
            'classes': [],
            'properties': [],
            'individuals': [],
            'movies_found': [],
            'sample_triples': [],
            'namespaces': []
        }
        
        try:
            # Obtener namespaces
            for prefix, uri in graph.namespaces():
                analysis['namespaces'].append({'prefix': prefix, 'uri': str(uri)})
            
            # Primero intentar consulta específica para películas
            try:
                simple_movies_query = """
                    PREFIX onto: <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    SELECT ?movie ?title WHERE {
                        ?movie rdf:type onto:Pelicula .
                        ?movie onto:nombrePelicula ?title .
                    } LIMIT 10
                """
                
                simple_results = list(graph.query(simple_movies_query))
                logger.info(f"Query específica encontró {len(simple_results)} películas")
                
                for row in simple_results:
                    try:
                        if len(row) >= 2:
                            movie_info = {
                                'uri': str(row[0]),
                                'title': str(row[1]),
                                'type': 'onto:Pelicula',
                                'local_name': str(row[0]).split('#')[-1] if '#' in str(row[0]) else str(row[0]).split('/')[-1]
                            }
                            analysis['movies_found'].append(movie_info)
                    except Exception as row_error:
                        logger.warning(f"Error procesando fila de película: {row_error}")
                        
                logger.info(f"Encontradas {len(analysis['movies_found'])} películas específicas")
                
            except Exception as e:
                logger.warning(f"No se pudieron encontrar películas específicas: {e}")
            
            # Buscar clases OWL
            classes_query = """
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?class ?label WHERE {
                    { ?class a owl:Class } UNION { ?class a rdfs:Class }
                    OPTIONAL { ?class rdfs:label ?label }
                } LIMIT 20
            """
            
            for row in graph.query(classes_query):
                if len(row) >= 1:
                    class_info = {
                        'uri': str(row[0]),
                        'label': str(row[1]) if len(row) > 1 and row[1] else 'Sin etiqueta',
                        'local_name': str(row[0]).split('#')[-1] if '#' in str(row[0]) else str(row[0]).split('/')[-1]
                    }
                    analysis['classes'].append(class_info)
            
            # Buscar propiedades
            properties_query = """
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?prop ?label WHERE {
                    { ?prop a owl:ObjectProperty } UNION
                    { ?prop a owl:DatatypeProperty } UNION
                    { ?prop a rdf:Property }
                    OPTIONAL { ?prop rdfs:label ?label }
                } LIMIT 20
            """
            
            for row in graph.query(properties_query):
                if len(row) >= 1:
                    prop_info = {
                        'uri': str(row[0]),
                        'label': str(row[1]) if len(row) > 1 and row[1] else 'Sin etiqueta',
                        'local_name': str(row[0]).split('#')[-1] if '#' in str(row[0]) else str(row[0]).split('/')[-1]
                    }
                    analysis['properties'].append(prop_info)
            
            # Buscar individuos que podrían ser películas (solo si no encontramos películas específicas)
            if len(analysis['movies_found']) == 0:
                movies_query = """
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX onto: <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
                    SELECT DISTINCT ?movie ?title ?type WHERE {
                        ?movie rdf:type ?type .
                        OPTIONAL { 
                            { ?movie onto:nombrePelicula ?title } UNION
                            { ?movie rdfs:label ?title }
                        }
                        FILTER(
                            regex(str(?type), "Pelicula", "i") ||
                            regex(str(?type), "Movie", "i") ||
                            regex(str(?type), "Film", "i") ||
                            regex(str(?movie), "pelicula", "i") ||
                            regex(str(?movie), "movie", "i") ||
                            regex(str(?movie), "film", "i")
                        )
                    } LIMIT 15
                """
                
                for row in graph.query(movies_query):
                    if len(row) >= 1:
                        movie_info = {
                            'uri': str(row[0]),
                            'title': str(row[1]) if len(row) > 1 and row[1] else 'Sin título',
                            'type': str(row[2]) if len(row) > 2 and row[2] else 'Sin tipo',
                            'local_name': str(row[0]).split('#')[-1] if '#' in str(row[0]) else str(row[0]).split('/')[-1]
                        }
                        analysis['movies_found'].append(movie_info)
            
            # Muestra de triples para entender la estructura
            count = 0
            for s, p, o in graph:
                if count >= 15:
                    break
                analysis['sample_triples'].append({
                    'subject': str(s)[:100] + '...' if len(str(s)) > 100 else str(s),
                    'predicate': str(p)[:100] + '...' if len(str(p)) > 100 else str(p),
                    'object': str(o)[:100] + '...' if len(str(o)) > 100 else str(o)
                })
                count += 1
                
        except Exception as e:
            analysis['error'] = str(e)
            logger.error(f"Error analizando contenido del grafo: {e}")
            
        return analysis

    def populate_from_dbpedia(self, dbpedia_rows: list, save_to: str = None):
        from rdflib import URIRef, Literal, RDF

        created = 0

        for dbp_movie in dbpedia_rows:

            # 1) Crear URI de película
            movie_title = dbp_movie.get("rdfs:label", "PeliculaDesconocida")
            movie_uri = URIRef(LOCAL_NS + movie_title.replace(" ", "_"))

            # Declarar tipo Pelicula
            self.graph.add((movie_uri, RDF.type, self.namespace["Pelicula"]))

            # 2) Propiedades literales simples
            for dbp_prop, local_prop in PROPERTY_MAPPING.items():
                if dbp_prop in dbp_movie:
                    self.graph.add((movie_uri, self.namespace[local_prop], Literal(dbp_movie[dbp_prop])))

            # 3) Relaciones con actores / directores / distribuidores
            for dbp_rel, rel_map in RELATION_MAPPING.items():

                if dbp_rel not in dbp_movie:
                    continue

                entries = dbp_movie[dbp_rel]
                if not isinstance(entries, list):
                    entries = [entries]

                for entry in entries:

                    # Crear individuo (actor, director, etc.)
                    ind_uri = URIRef(LOCAL_NS + entry["nombre"].replace(" ", "_"))
                    self.graph.add((ind_uri, RDF.type, self.namespace[rel_map["local_class"]]))

                    # Asignar propiedades mapeadas
                    for local_attr, dbp_attr in rel_map["properties"].items():

                        # soporte para: nombre, dbo:nombre, etc.
                        value = entry.get(dbp_attr, entry.get(dbp_attr.split(":")[-1], "Desconocido"))

                        self.graph.add((ind_uri, self.namespace[local_attr], Literal(value)))

                    # Relación película → actor/director/etc.
                    self.graph.add((movie_uri, self.namespace[rel_map["local_property"]], ind_uri))

            created += 1

        if save_to:
            self.graph.serialize(save_to, format="xml")

        return {"inserted": created}
