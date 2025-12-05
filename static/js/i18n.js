/**
 * Sistema de internacionalización (i18n) centralizado
 * Todas las traducciones se manejan desde aquí
 */

const i18n = {
    es: {
        // Header y navegación
        searchTitle: 'PELÍCULAS',
        searchSubtitle: 'Buscador semántico de películas',

        // Formulario de búsqueda
        searchPlaceholder: 'Buscar películas por título, director o actor...',
        searchButton: 'Buscar',

        // Estados de carga
        loading: 'Buscando...',
        consultingDatabases: 'Consultando bases de datos...',

        // Pestañas
        tabAll: 'Todos',
        tabLocal: 'Local',
        tabExternal: 'DBpedia',
        tabReduced: 'DBpedia Local',

        // Estados de resultados
        noResults: 'No se encontraron resultados',
        noResultsText: 'Intenta con otros términos de búsqueda.',
        searchError: 'Error en la búsqueda',
        unexpectedError: 'Ha ocurrido un error inesperado.',

        // Detalles de películas
        director: 'Director',
        year: 'Año',
        duration: 'Duración',
        genre: 'Género',
        seeMore: 'Ver más',

        // Estados vacíos
        noLocalResults: 'Sin resultados locales',
        noLocalResultsText: 'No se encontraron películas en tu ontología local.',
        noExternalResults: 'Sin resultados de DBpedia',
        noExternalResultsText: 'No se encontraron películas en DBpedia.',
        noReducedResults: 'Sin resultados de DBpedia Local',
        noReducedResultsText: 'No se encontraron películas en DBpedia Local.',

        // Estadísticas
        localMovies: 'Películas Locales',
        directors: 'Directores',
        rdfTriples: 'Triples RDF',

        // Mensajes del sistema
        enterSearchTerm: 'Por favor ingresa un término de búsqueda',

        // Fuentes de datos
        localOntology: 'Ontología Local',
        dbpedia: 'DBpedia',
        dbpediaReduced: 'DBpedia Local',

        // Footer
        footerTitle: 'Buscador Semántico de Películas',
        footerSubtitle: 'Web Semánticas - Proyecto académico',

        // Conectividad
        connectivityOnline: 'Conectado - Búsqueda online',
        connectivityOffline: 'Sin conexión - Búsqueda offline',
        checking: 'Verificando...'
    },

    en: {
        // Header and navigation
        searchTitle: 'MOVIES',
        searchSubtitle: 'Semantic movie search engine',

        // Search form
        searchPlaceholder: 'Search movies by title, director or actor...',
        searchButton: 'Search',

        // Loading states
        loading: 'Searching...',
        consultingDatabases: 'Querying databases...',

        // Tabs
        tabAll: 'All',
        tabLocal: 'Local',
        tabExternal: 'DBpedia',
        tabReduced: 'Local DBpedia',

        // Result states
        noResults: 'No results found',
        noResultsText: 'Try different search terms.',
        searchError: 'Search error',
        unexpectedError: 'An unexpected error occurred.',

        // Movie details
        director: 'Director',
        year: 'Year',
        duration: 'Duration',
        genre: 'Genre',
        seeMore: 'See more',

        // Empty states
        noLocalResults: 'No local results',
        noLocalResultsText: 'No movies found in your local ontology.',
        noExternalResults: 'No DBpedia results',
        noExternalResultsText: 'No movies found in DBpedia.',
        noReducedResults: 'No local DBpedia results',
        noReducedResultsText: 'No movies found in local DBpedia.',

        // Statistics
        localMovies: 'Local Movies',
        directors: 'Directors',
        rdfTriples: 'RDF Triples',

        // System messages
        enterSearchTerm: 'Please enter a search term',

        // Data sources
        localOntology: 'Local Ontology',
        dbpedia: 'DBpedia',
        dbpediaReduced: 'Local DBpedia',

        // Footer
        footerTitle: 'Semantic Movie Search',
        footerSubtitle: 'Semantic Web - Academic project',

        // Connectivity
        connectivityOnline: 'Connected - Online search',
        connectivityOffline: 'Offline - Local search only',
        checking: 'Checking...'
    },

    fr: {
        // En-tête et navigation
        searchTitle: 'FILMS',
        searchSubtitle: 'Moteur de recherche sémantique de films',

        // Formulaire de recherche
        searchPlaceholder: 'Rechercher des films par titre, réalisateur ou acteur...',
        searchButton: 'Rechercher',

        // États de chargement
        loading: 'Recherche...',
        consultingDatabases: 'Consultation des bases de données...',

        // Onglets
        tabAll: 'Tous',
        tabLocal: 'Local',
        tabExternal: 'DBpedia',
        tabReduced: 'DBpedia Local',

        // États de résultats
        noResults: 'Aucun résultat trouvé',
        noResultsText: 'Essayez avec d\'autres termes.',
        searchError: 'Erreur de recherche',
        unexpectedError: 'Une erreur inattendue s\'est produite.',

        // Détails du film
        director: 'Réalisateur',
        year: 'Année',
        duration: 'Durée',
        genre: 'Genre',
        seeMore: 'Voir plus',

        // États vides
        noLocalResults: 'Aucun résultat local',
        noLocalResultsText: 'Aucun film trouvé dans votre ontologie locale.',
        noExternalResults: 'Aucun résultat DBpedia',
        noExternalResultsText: 'Aucun film trouvé dans DBpedia.',
        noReducedResults: 'Aucun résultat DBpedia Local',
        noReducedResultsText: 'Aucun film trouvé dans DBpedia Local.',

        // Statistiques
        localMovies: 'Films Locaux',
        directors: 'Réalisateurs',
        rdfTriples: 'Triples RDF',

        // Messages système
        enterSearchTerm: 'Veuillez entrer un terme de recherche',

        // Sources de données
        localOntology: 'Ontologie Locale',
        dbpedia: 'DBpedia',
        dbpediaReduced: 'DBpedia Local',

        // Pied de page
        footerTitle: 'Recherche Sémantique de Films',
        footerSubtitle: 'Web Sémantique - Projet académique',

        // Connectivité
        connectivityOnline: 'Connecté - Recherche en ligne',
        connectivityOffline: 'Hors ligne - Recherche locale uniquement',
        checking: 'Vérification...'
    },

    de: {
        // Kopfzeile und Navigation
        searchTitle: 'FILME',
        searchSubtitle: 'Semantische Filmsuchmaschine',

        // Suchformular
        searchPlaceholder: 'Filme nach Titel, Regisseur oder Schauspieler suchen...',
        searchButton: 'Suchen',

        // Ladezustände
        loading: 'Suche...',
        consultingDatabases: 'Datenbanken werden abgefragt...',

        // Registerkarten
        tabAll: 'Alle',
        tabLocal: 'Lokal',
        tabExternal: 'DBpedia',
        tabReduced: 'Lokale DBpedia',

        // Ergebniszustände
        noResults: 'Keine Ergebnisse gefunden',
        noResultsText: 'Versuchen Sie andere Suchbegriffe.',
        searchError: 'Suchfehler',
        unexpectedError: 'Ein unerwarteter Fehler ist aufgetreten.',

        // Filmdetails
        director: 'Regisseur',
        year: 'Jahr',
        duration: 'Dauer',
        genre: 'Genre',
        seeMore: 'Mehr sehen',

        // Leere Zustände
        noLocalResults: 'Keine lokalen Ergebnisse',
        noLocalResultsText: 'Keine Filme in Ihrer lokalen Ontologie gefunden.',
        noExternalResults: 'Keine DBpedia-Ergebnisse',
        noExternalResultsText: 'Keine Filme in DBpedia gefunden.',
        noReducedResults: 'Keine lokalen DBpedia-Ergebnisse',
        noReducedResultsText: 'Keine Filme in lokaler DBpedia gefunden.',

        // Statistiken
        localMovies: 'Lokale Filme',
        directors: 'Regisseure',
        rdfTriples: 'RDF-Tripel',

        // Systemmeldungen
        enterSearchTerm: 'Bitte geben Sie einen Suchbegriff ein',

        // Datenquellen
        localOntology: 'Lokale Ontologie',
        dbpedia: 'DBpedia',
        dbpediaReduced: 'Lokale DBpedia',

        // Fußzeile
        footerTitle: 'Semantische Filmsuche',
        footerSubtitle: 'Semantisches Web - Akademisches Projekt',

        // Konnektivität
        connectivityOnline: 'Verbunden - Online-Suche',
        connectivityOffline: 'Offline - Nur lokale Suche',
        checking: 'Überprüfen...'
    }
};

/**
 * Gestor de internacionalización
 */
class I18nManager {
    constructor() {
        this.currentLanguage = 'es';
        this.translations = i18n;
    }

    /**
     * Cambia el idioma actual y actualiza la interfaz
     */
    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLanguage = lang;
            this.updateUI();
            this.updateHtmlLang(lang);

            // Guardar preferencia en localStorage
            try {
                localStorage.setItem('preferred_language', lang);
            } catch (e) {
                console.warn('No se pudo guardar la preferencia de idioma');
            }
        }
    }

    /**
     * Obtiene una traducción por clave
     */
    t(key) {
        return this.translations[this.currentLanguage][key] || key;
    }

    /**
     * Actualiza todos los elementos de la interfaz
     */
    updateUI() {
        // Actualizar elementos con data-i18n (texto)
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const value = this.t(key);
            el.textContent = value;
        });

        // Actualizar placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const value = this.t(key);
            el.placeholder = value;
        });

        // Actualizar títulos (title attribute)
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            const value = this.t(key);
            el.title = value;
        });

        // Actualizar valores de aria-label para accesibilidad
        document.querySelectorAll('[data-i18n-aria]').forEach(el => {
            const key = el.getAttribute('data-i18n-aria');
            const value = this.t(key);
            el.setAttribute('aria-label', value);
        });
    }

    /**
     * Actualiza el atributo lang del documento HTML
     */
    updateHtmlLang(lang) {
        document.documentElement.lang = lang;
    }

    /**
     * Obtiene el idioma guardado en localStorage o el idioma del navegador
     */
    getPreferredLanguage() {
        try {
            // Intentar obtener de localStorage
            const saved = localStorage.getItem('preferred_language');
            if (saved && this.translations[saved]) {
                return saved;
            }
        } catch (e) {
            console.warn('No se pudo acceder a localStorage');
        }

        // Detectar idioma del navegador
        const browserLang = navigator.language.split('-')[0];
        return this.translations[browserLang] ? browserLang : 'es';
    }

    /**
     * Inicializa el idioma al cargar la página
     */
    initialize() {
        const preferredLang = this.getPreferredLanguage();
        this.setLanguage(preferredLang);

        // Actualizar el selector si existe
        const langSelector = document.getElementById('language');
        if (langSelector) {
            langSelector.value = preferredLang;
        }
    }
}

// Crear instancia global
window.i18nManager = new I18nManager();