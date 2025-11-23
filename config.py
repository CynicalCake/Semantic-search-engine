import os

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    ONTOLOGY_FILE = 'OntologiaPeliculasV5.owl'
    DBPEDIA_ENDPOINT = 'http://dbpedia.org/sparql'
    DEBUG = True
    HOST = '127.0.0.1'
    PORT = 5000
    
    # Configuración de paginación
    RESULTS_PER_PAGE = 10
    MAX_RESULTS = 50
    
    # Configuración de idiomas soportados
    SUPPORTED_LANGUAGES = {
        'es': 'Español',
        'en': 'English',
        'fr': 'Français',
        'de': 'Deutsch'
    }
    
    # Configuración de cache (para futuras mejoras)
    CACHE_TIMEOUT = 300  # 5 minutos

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}