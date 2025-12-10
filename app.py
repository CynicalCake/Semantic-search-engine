from flask import Flask, request, render_template, jsonify
from services.ontology_service import OntologyService
from services.dbpedia_service import DBpediaService
from services.dbpedia_reduced_service import DBpediaReducedService
from services.ner_service import NERService
from services.intent_service import IntentService
from services.tmdb_service import TMDBService
from config import Config
from datetime import datetime
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar servicios
ontology_service = OntologyService(app.config['ONTOLOGY_FILE'])
dbpedia_service = DBpediaService()
dbpedia_reduced_service = DBpediaReducedService()
ner_service = NERService()
tmdb_service = TMDBService(api_key="a6e641c79b947ea3f97330b3b9928daf")
intent_service = IntentService(ner_service, tmdb_service)

def check_internet_connectivity():
    """Verifica si hay conectividad a internet"""
    try:
        # Intentar conectar a un endpoint para verificar la conectividad
        response = requests.get('https://httpbin.org/status/200', timeout=8)
        return response.status_code == 200
    except:
        try:
            # Fallback: intentar con Google
            response = requests.get('https://www.google.com', timeout=6)
            return response.status_code == 200
        except:
            try:
                # Último fallback: CloudFlare DNS
                response = requests.get('https://1.1.1.1', timeout=5)
                return True
            except:
                return False

@app.route('/')
def index():
    """Página principal del buscador"""
    return render_template('index.html')

@app.route('/about')
def about():
    """Página de información sobre la aplicación"""
    try:
        stats = ontology_service.get_stats()
        return render_template('about.html', stats=stats)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return render_template('about.html', stats={})

@app.route('/debug')
def debug():
    """Página de debug para diagnosticar la ontología"""
    return render_template('debug.html')

@app.route('/api/debug/ontology')
def debug_ontology():
    """API endpoint para obtener información de debug de la ontología"""
    try:
        debug_info = ontology_service.get_debug_info()
        return jsonify(debug_info)
    except Exception as e:
        logger.error(f"Error en debug de ontología: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/debug/test-query')
def test_query():
    """Endpoint para probar queries SPARQL específicas"""
    try:
        if len(ontology_service.graph) == 0:
            return jsonify({
                'error': 'Ontología no cargada - grafo vacío',
                'total_found': 0,
                'movies': [],
                'debug_info': {
                    'graph_size': len(ontology_service.graph),
                    'ontology_file': ontology_service.ontology_file
                }
            })
            
        # Query simple y segura
        test_query = """
            PREFIX onto: <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?pelicula ?titulo
            WHERE {
                ?pelicula rdf:type onto:Pelicula .
                ?pelicula onto:nombrePelicula ?titulo .
            }
            LIMIT 10
        """
        
        logger.info(f"Ejecutando query de prueba en grafo con {len(ontology_service.graph)} triples")
        
        results = list(ontology_service.graph.query(test_query))
        logger.info(f"Query ejecutada, {len(results)} resultados obtenidos")
        
        movies_list = []
        for i, row in enumerate(results):
            try:
                movie_data = {
                    'uri': str(row[0]) if len(row) > 0 else f'uri_missing_{i}',
                    'titulo': str(row[1]) if len(row) > 1 else f'titulo_missing_{i}'
                }
                movies_list.append(movie_data)
                logger.debug(f"Película {i}: {movie_data}")
            except Exception as row_error:
                logger.error(f"Error procesando fila {i}: {row_error}")
                movies_list.append({
                    'uri': f'error_row_{i}',
                    'titulo': f'Error procesando fila: {str(row_error)}'
                })
        
        response_data = {
            'total_found': len(movies_list),
            'movies': movies_list,
            'query_used': test_query.strip(),
            'debug_info': {
                'graph_size': len(ontology_service.graph),
                'results_count': len(results),
                'ontology_file': ontology_service.ontology_file
            }
        }
        
        logger.info(f"Retornando respuesta con {len(movies_list)} películas")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error en test query: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Error en servidor: {str(e)}',
            'total_found': 0,
            'movies': [],
            'debug_info': {
                'graph_size': len(ontology_service.graph) if hasattr(ontology_service, 'graph') else 'N/A',
                'exception_type': type(e).__name__
            }
        }), 500

@app.route('/api/debug/graph-status')
def graph_status():
    """Endpoint para verificar el estado del grafo"""
    try:
        return jsonify({
            'graph_loaded': ontology_service.graph is not None,
            'graph_size': len(ontology_service.graph) if ontology_service.graph else 0,
            'ontology_file': ontology_service.ontology_file,
            'ontology_path': getattr(ontology_service, 'ontology_path', 'No definido'),
            'namespaces': [{'prefix': str(p), 'uri': str(u)} for p, u in ontology_service.graph.namespaces()] if ontology_service.graph else []
        })
    except Exception as e:
        logger.error(f"Error verificando estado del grafo: {e}")
        return jsonify({
            'error': str(e),
            'graph_loaded': False,
            'graph_size': 0
        }), 500

@app.route('/api/connectivity')
def api_connectivity():
    """Verifica el estado de conectividad"""
    try:
        is_online = check_internet_connectivity()
        return jsonify({
            'online': is_online,
            'status': 'connected' if is_online else 'offline',
            'timestamp': str(datetime.now())
        })
    except Exception as e:
        logger.error(f"Error verificando conectividad: {e}")
        return jsonify({
            'online': False,
            'status': 'offline',
            'error': str(e),
            'timestamp': str(datetime.now())
        })

def api_search(term, language):
    """Búsqueda clásica interna, reusable desde otro endpoint"""
    try:
        if not term:
            return jsonify({'error': 'Término de búsqueda requerido'}), 400

        is_online = check_internet_connectivity()

        if is_online:
            logger.info("Búsqueda clásica en modo online: usando solo DBpedia")
            local_results = []
            external_results = dbpedia_service.search_movies(term, language)
            reduced_results = []
        else:
            logger.info("Búsqueda clásica en modo offline: usando ontología local y DBpedia reducida")
            local_results = ontology_service.search_movies(term)
            external_results = []
            reduced_results = dbpedia_reduced_service.search_movies(term)

        return jsonify({
            'local': local_results,
            'external': external_results,
            'reduced': reduced_results,
            'total': len(local_results) + len(external_results) + len(reduced_results),
            'online_mode': is_online
        })
    except Exception as e:
        logger.error(f"Error en api_search: {e}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500

def semantic_search(query, language):
    """Búsqueda semántica interna, reusable desde otro endpoint"""
    try:
        if not query:
            return jsonify({"error": "Se requiere parámetro ?q"}), 400

        # Detectar intenciones y entidades
        intent_data = intent_service.detect_intent(query, language)
        intents = intent_data.get("intents", {})

        persons = intent_data.get("persons", [])
        roles = intent_data.get("roles", {})
        years = intent_data.get("years", [])
        genres = intent_data.get("genres", [])
        studios = intent_data.get("studios", [])

        actor = roles.get("actor")
        actor = actor[0] if actor else None

        director = roles.get("director")
        director = director[0] if director else None

        year = years[0] if years else None
        genre = genres[0] if genres else None
        studio = studios[0] if studios else None

        if not any(intents.values()):
            return jsonify({
                "error": "No se pudo entender la intención de la consulta",
                "debug": {
                    "persons": persons,
                    "roles": roles,
                    "years": years,
                    "genres": genres,
                    "studios": studios,
                    "intent_detected": intents
                }
            }), 400

        is_online = check_internet_connectivity()
        print (actor, director, year, genre, studio, language)
        if is_online:
            logger.info("Búsqueda semántica en modo online: usando solo DBpedia")
            local_results = []
            external_results = dbpedia_service.search_movies_semantic(
                actor=actor, 
                director=director, 
                year=year, 
                genre=genre, 
                studio=studio, 
                language=language
            )
            reduced_results = []
        else:
            logger.info("Búsqueda semántica en modo offline: usando ontología local y DBpedia reducida")
            local_results = ontology_service.search_movies_semantic(
                actor=actor, 
                director=director, 
                year=year, 
                genre=genre, 
                studio=studio, 
                language=language
            )
            external_results = []
            reduced_results = dbpedia_reduced_service.search_movies_semantic(
                actor=actor, 
                director=director, 
                year=year, 
                genre=genre
            )

        return jsonify({
            "query": query,
            "intents_detected": intents,
            "actor": actor,
            "director": director,
            "year": year,
            "genre": genre,
            "local_count": len(local_results),
            "external_count": len(external_results),
            "reduced_count": len(reduced_results),
            "local": local_results,
            "external": external_results,
            "reduced": reduced_results,
            "total": len(local_results) + len(external_results) + len(reduced_results),
            "online_mode": is_online
        })

    except Exception as e:
        logger.error(f"Error en semantic_search: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_auto')
def search_auto():
    term = request.args.get('q', '').strip()
    language = request.args.get('lang', 'es')

    if not term:
        return jsonify({'error': 'Se requiere parámetro ?q'}), 400

    # Detectar intención para decidir
    intent_data = intent_service.detect_intent(term, language)
    intents = intent_data.get("intents", {})

    if any(intents.values()):
        # Hay intención, usar búsqueda semántica
        return semantic_search(term, language)
    else:
        # Solo nombre de película, usar búsqueda clásica
        return api_search(term, language)

@app.route('/api/stats')
def api_stats():
    """Estadísticas de la ontología"""
    try:
        stats = ontology_service.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': 'Error obteniendo estadísticas'}), 500

@app.route('/api/health')
def api_health():
    """Health check del servicio"""
    try:
        # Verificar ontología local
        local_status = len(ontology_service.graph) > 0
        
        # Verificar DBpedia
        dbpedia_status = dbpedia_service.health_check()
        
        # Verificar DBpedia reducida
        reduced_status = dbpedia_reduced_service.health_check()
        
        return jsonify({
            'status': 'healthy' if (local_status and reduced_status) else 'partial',
            'local_ontology': local_status,
            'dbpedia': dbpedia_status,
            'dbpedia_reduced': reduced_status,
            'timestamp': str(datetime.now())
        })
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/reduced/stats')
def api_reduced_stats():
    """Estadísticas de DBpedia reducida"""
    try:
        stats = dbpedia_reduced_service.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de DBpedia reducida: {e}")
        return jsonify({'error': 'Error obteniendo estadísticas'}), 500

@app.route('/api/reduced/update', methods=['POST'])
def api_reduced_update():
    """Fuerza actualización de DBpedia reducida"""
    try:
        dbpedia_reduced_service.force_update()
        return jsonify({
            'status': 'success',
            'message': 'Actualización iniciada',
            'timestamp': str(datetime.now())
        })
    except Exception as e:
        logger.error(f"Error actualizando DBpedia reducida: {e}")
        return jsonify({'error': 'Error en actualización'}), 500

@app.route('/api/reduced/expand', methods=['POST'])
def api_reduced_expand():
    """Expande la base de datos de DBpedia reducida"""
    try:
        data = request.get_json() or {}
        additional_movies = data.get('additional_movies', 1000)
        
        # Validar límite razonable
        if additional_movies > 5000:
            additional_movies = 5000
        elif additional_movies < 100:
            additional_movies = 100
            
        added_count = dbpedia_reduced_service.expand_database(additional_movies)
        current_stats = dbpedia_reduced_service.get_stats()
        
        return jsonify({
            'status': 'success',
            'message': f'Base de datos expandida con {added_count} películas',
            'added_movies': added_count,
            'total_movies': current_stats['peliculas'],
            'total_triples': current_stats['triples_total'],
            'timestamp': str(datetime.now())
        })
    except Exception as e:
        logger.error(f"Error expandiendo DBpedia reducida: {e}")
        return jsonify({'error': 'Error expandiendo base de datos'}), 500

@app.route('/api/reduced/recommendations')
def api_reduced_recommendations():
    """Obtiene recomendaciones de tamaño para la base de datos"""
    try:
        recommendations = dbpedia_reduced_service.get_recommended_size()
        current_count = dbpedia_reduced_service.get_movie_count()
        
        return jsonify({
            'current_movies': current_count,
            'recommendations': recommendations,
            'timestamp': str(datetime.now())
        })
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {e}")
        return jsonify({'error': 'Error obteniendo recomendaciones'}), 500

@app.errorhandler(404)
def not_found_error(error):
    """Maneja errores 404"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Maneja errores 500"""
    logger.error(f"Error interno: {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Maneja excepciones no controladas"""
    logger.error(f"Excepción no controlada: {error}", exc_info=True)
    return render_template('errors/500.html'), 500

@app.post("/api/ontology/save_movie")
def save_movie():
    data = request.json
    try:
        uri = ontology_service.save_movie_from_external(data)
        return {"success": True, "uri": uri}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


if __name__ == '__main__':
    logger.info("Iniciando CinemaSearch - Buscador Semántico de Películas")
    logger.info(f"Ontología: {app.config['ONTOLOGY_FILE']}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    
    app.run(
        debug=True,  # Temporal: desactivar debug para evitar problemas con spacy
        host=app.config.get('HOST', '127.0.0.1'),
        port=app.config.get('PORT', 5000)
    )