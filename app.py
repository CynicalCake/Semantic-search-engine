from flask import Flask, request, render_template, jsonify
from services.ontology_service import OntologyService
from services.dbpedia_service import DBpediaService
from config import Config
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar servicios
ontology_service = OntologyService(app.config['ONTOLOGY_FILE'])
dbpedia_service = DBpediaService()

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

@app.route('/api/search')
def api_search():
    """Endpoint API para búsquedas AJAX"""
    term = request.args.get('term', '')
    language = request.args.get('lang', 'es')
    
    if not term:
        return jsonify({'error': 'Término de búsqueda requerido'}), 400
    
    try:
        local_results = ontology_service.search_movies(term)
        external_results = dbpedia_service.search_movies(term, language)
        
        return jsonify({
            'local': local_results,
            'external': external_results,
            'total': len(local_results) + len(external_results)
        })
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

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
        
        return jsonify({
            'status': 'healthy' if local_status else 'partial',
            'local_ontology': local_status,
            'dbpedia': dbpedia_status,
            'timestamp': str(datetime.now())
        })
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

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

if __name__ == '__main__':
    logger.info("Iniciando CinemaSearch - Buscador Semántico de Películas")
    logger.info(f"Ontología: {app.config['ONTOLOGY_FILE']}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    
    app.run(
        debug=app.config.get('DEBUG', False),
        host=app.config.get('HOST', '127.0.0.1'),
        port=app.config.get('PORT', 5000)
    )