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