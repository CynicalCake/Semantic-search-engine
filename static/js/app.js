/**
 * CinemaSearch - Aplicación de búsqueda semántica de películas
 * Versión con sistema de internacionalización integrado
 */

class CinemaSearch {
    constructor() {
        this.currentResults = {
            local: [],
            external: [],
            reduced: [],
            all: []
        };
        this.isSearching = false;
        this.debounceTimer = null;
        this.connectivityStatus = null;

        // Esperar a que i18n esté disponible
        if (window.i18nManager) {
            this.i18n = window.i18nManager;
            this.i18n.initialize();
        } else {
            console.error('Sistema i18n no disponible');
        }

        this.initializeEventListeners();
        this.loadInitialStats();
        this.startConnectivityMonitoring();
    }

    /**
     * Inicializa todos los event listeners
     */
    initializeEventListeners() {
        const searchForm = document.getElementById('searchForm');
        const searchInput = document.getElementById('searchTerm');
        const langSelector = document.getElementById('language');

        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }

        if (searchInput) {
            searchInput.addEventListener('focus', () => this.handleInputFocus());
        }

        // Listener para cambio de idioma
        if (langSelector) {
            langSelector.addEventListener('change', (e) => {
                this.i18n.setLanguage(e.target.value);

                // Si hay resultados, re-renderizarlos en el nuevo idioma
                if (this.currentResults.all.length > 0) {
                    this.displayResults();
                }
            });
        }

        // Manejar cambios de pestaña
        const tabButtons = document.querySelectorAll('[data-bs-toggle="pill"]');
        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', (e) => this.handleTabChange(e));
        });
    }

    /**
     * Maneja el envío del formulario de búsqueda
     */
    async handleSearch(event) {
        event.preventDefault();

        const searchTerm = document.getElementById('searchTerm').value.trim();
        const language = document.getElementById('language').value;

        if (!searchTerm) {
            this.showAlert(this.i18n.t('enterSearchTerm'), 'warning');
            return;
        }

        await this.performSearch(searchTerm, language);
    }

    /**
     * Maneja el foco en el input de búsqueda
     */
    handleInputFocus() {
        const searchInput = document.getElementById('searchTerm');
        if (searchInput.value.trim() === '') {
            this.clearResults();
        }
    }

    /**
     * Realiza la búsqueda utilizando la API
     */
    async performSearch(term, language) {
        if (this.isSearching) return;

        this.isSearching = true;
        this.showLoading(true);
        this.hideResults();

        try {
            const lower = term.toLowerCase();

            const url = `/api/search_auto?q=${encodeURIComponent(term)}&lang=${language}`;
            console.log("➡ Usando búsqueda SEMÁNTICA:", url);
            
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.currentResults = {
                local: data.local || [],
                external: data.external || [],
                reduced: data.reduced || [],
                all: [...(data.local || []), ...(data.external || []), ...(data.reduced || [])]
            };

            this.displayResults();

        } catch (error) {
            console.error("Error en la búsqueda:", error);
            this.showError(error.message);

        } finally {
            this.isSearching = false;
            this.showLoading(false);
        }
    }

    /**
     * Muestra el indicador de carga
     */
    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.classList.toggle('d-none', !show);
        }
    }

    /**
     * Muestra los resultados de búsqueda
     */
    displayResults() {
        const resultsSection = document.getElementById('resultsSection');
        const noResults = document.getElementById('noResults');

        if (this.currentResults.all.length === 0) {
            resultsSection?.classList.add('d-none');
            noResults?.classList.remove('d-none');
            return;
        }

        this.updateTabCounts();

        this.renderMovieResults('allResults', this.currentResults.all);
        this.renderMovieResults('localResults', this.currentResults.local);
        this.renderMovieResults('externalResults', this.currentResults.external);
        this.renderMovieResults('reducedResults', this.currentResults.reduced);

        resultsSection?.classList.remove('d-none');
        noResults?.classList.add('d-none');
        this.hideError();
    }

    /**
     * Actualiza los contadores en las pestañas
     */
    updateTabCounts() {
        const counts = {
            'allCount': this.currentResults.all.length,
            'localCount': this.currentResults.local.length,
            'externalCount': this.currentResults.external.length,
            'reducedCount': this.currentResults.reduced.length
        };

        Object.entries(counts).forEach(([id, count]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = count;
        });
    }

    /**
     * Renderiza los resultados de películas en el contenedor especificado
     */
    renderMovieResults(containerId, movies) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (movies.length === 0) {
            container.innerHTML = this.getEmptyStateHtml(containerId);
            return;
        }

        container.innerHTML = movies.map(movie => this.createMovieCard(movie)).join('');
        this.animateCards(container);
    }

    /**
     * Crea una tarjeta HTML para una película
     */
    createMovieCard(movie) {
        let sourceClass = 'external';
        let sourceText = this.i18n.t('dbpedia');

        if (movie.tipo === 'local') {
            sourceClass = 'local';
            sourceText = this.i18n.t('localOntology');
        } else if (movie.tipo === 'reduced') {
            sourceClass = 'reduced';
            sourceText = this.i18n.t('dbpediaReduced');
        }

        if (movie.fuente) {
            sourceText = movie.fuente;
        }

        const shouldShowMoreButton = movie.uri &&
            (movie.tipo !== 'local' && movie.tipo !== 'reduced');

        const shouldShowLocalSave = 
            (movie.tipo !== 'local' && movie.tipo !== 'reduced');

        // Función para truncar listas largas
        const maxItems = 5;
        const formatList = (list) => {
            if (!list || !list.length) return 'No disponible';
            if (list.length <= maxItems) return list.join(", ");
            return list.slice(0, maxItems).join(", ") + " ...";
        };

        return `
        <div class="movie-card ${sourceClass}">

            ${shouldShowLocalSave ? `
                <button class="save-local-icon" title="Guardar en local"
                    data-movie='${JSON.stringify(movie)}'>
                    💾
                </button>
            ` : ''}

            <div class="card-content">
                <!-- IZQUIERDA: Poster -->
                <div class="card-left">
                    ${movie.poster ? `<img src="${movie.poster}" class="movie-poster"/>` : ''}
                    <span class="source-badge ${sourceClass}">${sourceText}</span>
                </div>

                <!-- DERECHA: Texto -->
                <div class="card-right">
                    <div class="movie-details-top">
                        ${movie.anio ? `<span class="detail-item">${this.i18n.t('year')}: ${this.escapeHtml(movie.anio)}</span>` : ''}
                        ${movie.duracion ? `<span class="detail-item">${this.i18n.t('duration')}: ${this.escapeHtml(movie.duracion)}</span>` : ''}
                    </div>

                    <h3 class="movie-title">${this.escapeHtml(movie.titulo)}</h3>

                    ${movie.generos ? `
                        <div class="detail-item genres">
                            ${this.escapeHtml(movie.generos.join(" • "))}
                        </div>
                    ` : ''}

                    ${movie.directores ? `<div class="movie-director">${this.i18n.t('director')}: ${this.escapeHtml(formatList(movie.directores))}</div>` : ''}
                    ${movie.actores ? `<div class="movie-actors">${this.i18n.t('actors')}: ${this.escapeHtml(formatList(movie.actores))}</div>` : ''}

                    ${movie.sinopsis ? `<p class="movie-synopsis">${this.escapeHtml(movie.sinopsis)}</p>` : ''}

                    <div class="movie-meta">
                        ${shouldShowMoreButton ? `
                            <a href="${movie.uri}" target="_blank" class="btn btn-outline-secondary btn-sm">
                                ${this.i18n.t('seeMore')}
                            </a>
                        ` : ''}
                    </div>
                </div>
            </div>

        </div>
        `;
        }


    /**
     * Genera HTML para estado vacío
     */
    getEmptyStateHtml(containerId) {
        const messages = {
            'localResults': {
                title: this.i18n.t('noLocalResults'),
                text: this.i18n.t('noLocalResultsText')
            },
            'externalResults': {
                title: this.i18n.t('noExternalResults'),
                text: this.i18n.t('noExternalResultsText')
            },
            'reducedResults': {
                title: this.i18n.t('noReducedResults'),
                text: this.i18n.t('noReducedResultsText')
            }
        };

        const config = messages[containerId] || {
            title: this.i18n.t('noResults'),
            text: this.i18n.t('noResultsText')
        };

        return `
            <div class="text-center py-4">
                <h5 class="text-muted">${config.title}</h5>
                <p class="text-muted">${config.text}</p>
            </div>
        `;
    }

    /**
     * Añade animación a las tarjetas
     */
    animateCards(container) {
        const cards = container.querySelectorAll('.movie-card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'all 0.6s ease';

                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50);
            }, index * 100);
        });
    }

    /**
     * Maneja el cambio entre pestañas
     */
    handleTabChange(event) {
        const targetPane = event.target.getAttribute('data-bs-target');
        console.log(`Cambiando a pestaña: ${targetPane}`);
    }

    /**
     * Oculta la sección de resultados
     */
    hideResults() {
        const resultsSection = document.getElementById('resultsSection');
        const noResults = document.getElementById('noResults');

        resultsSection?.classList.add('d-none');
        noResults?.classList.add('d-none');
    }

    /**
     * Limpia todos los resultados
     */
    clearResults() {
        this.currentResults = { local: [], external: [], reduced: [], all: [] };
        this.hideResults();
        this.hideError();
    }

    /**
     * Muestra un error
     */
    showError(message) {
        const errorState = document.getElementById('errorState');
        const errorMessage = document.getElementById('errorMessage');

        if (errorState && errorMessage) {
            errorMessage.textContent = message;
            errorState.classList.remove('d-none');
        } else {
            this.showAlert(message, 'error');
        }

        this.hideResults();
    }

    /**
     * Oculta el estado de error
     */
    hideError() {
        const errorState = document.getElementById('errorState');
        errorState?.classList.add('d-none');
    }

    /**
     * Muestra una alerta temporal
     */
    showAlert(message, type = 'info') {
        const alertTypes = {
            'info': 'alert-info',
            'warning': 'alert-warning',
            'error': 'alert-danger',
            'success': 'alert-success'
        };

        const alertHtml = `
            <div class="alert ${alertTypes[type]} alert-dismissible fade show" role="alert">
                <i class="fas fa-info-circle me-2"></i>
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const container = document.querySelector('.container') || document.body;
        const alertElement = document.createElement('div');
        alertElement.innerHTML = alertHtml;
        container.prepend(alertElement.firstElementChild);

        setTimeout(() => {
            const alert = document.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }

    /**
     * Carga las estadísticas iniciales
     */
    async loadInitialStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();

            if (stats.error) {
                console.warn('Error cargando estadísticas:', stats.error);
                return;
            }

            this.updateStatsDisplay(stats);

        } catch (error) {
            console.error('Error cargando estadísticas iniciales:', error);
        }
    }

    /**
     * Actualiza la visualización de estadísticas
     */
    updateStatsDisplay(stats) {
        const elements = {
            'totalMovies': stats.total_peliculas,
            'totalDirectors': stats.total_directores,
            'totalTriples': stats.total_triples
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element && value !== undefined) {
                this.animateCounter(element, value);
            }
        });
    }

    /**
     * Anima un contador numérico
     */
    animateCounter(element, targetValue) {
        const startValue = 0;
        const duration = 2000;
        const startTime = performance.now();

        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            const currentValue = Math.floor(startValue + (targetValue - startValue) * progress);
            element.textContent = currentValue.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };

        requestAnimationFrame(updateCounter);
    }

    /**
     * Inicia el monitoreo de conectividad
     */
    startConnectivityMonitoring() {
        this.checkConnectivity();
        setInterval(() => {
            this.checkConnectivity();
        }, 15000); // Reducir frecuencia de verificación a cada 15 segundos
    }

    /**
     * Verifica el estado de conectividad
     */
    async checkConnectivity() {
        try {
            const response = await fetch('/api/connectivity');
            const data = await response.json();

            this.connectivityStatus = data.online;
            this.updateConnectivityIndicator(data);

        } catch (error) {
            console.error('Error verificando conectividad:', error);
            this.connectivityStatus = false;
            this.updateConnectivityIndicator({
                online: false,
                status: 'offline',
                error: 'Error de conexión'
            });
        }
    }

    /**
     * Actualiza el indicador visual de conectividad
     */
    updateConnectivityIndicator(data) {
        const indicator = document.getElementById('connectivity-status');
        if (!indicator) return;

        if (data.online) {
            indicator.className = 'badge bg-success';
            indicator.innerHTML = `<i class="fas fa-wifi"></i> ${this.i18n.t('connectivityOnline')}`;
        } else {
            indicator.className = 'badge bg-warning';
            indicator.innerHTML = `<i class="fas fa-wifi-slash"></i> ${this.i18n.t('connectivityOffline')}`;
        }
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;

        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
    document.addEventListener("click", function (e) {
        if (e.target.classList.contains("save-local-icon")) {
            const movie = JSON.parse(e.target.dataset.movie);
            saveMovieToLocalOntology(movie);
        }
    });

    async function saveMovieToLocalOntology(movie) {
        const response = await fetch("/api/ontology/save_movie", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(movie)
        });

        const data = await response.json();

        if (data.success) {
            alert("Película guardada en la ontología.");
        } else {
            alert("Error: " + data.error);
        }
    }

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.cinemaSearch = new CinemaSearch();
});