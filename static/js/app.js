/**
 * CinemaSearch - Aplicación de búsqueda semántica de películas
 * Maneja la interacción con APIs y la actualización dinámica de la interfaz
 */

class CinemaSearch {
    constructor() {
        this.currentResults = {
            local: [],
            external: [],
            all: []
        };
        this.isSearching = false;
        this.debounceTimer = null;
        
        this.initializeEventListeners();
        this.loadInitialStats();
    }

    /**
     * Inicializa todos los event listeners
     */
    initializeEventListeners() {
        const searchForm = document.getElementById('searchForm');
        const searchInput = document.getElementById('searchTerm');
        
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }
        
        if (searchInput) {
            // Búsqueda en tiempo real con debounce
            //searchInput.addEventListener('input', (e) => this.handleLiveSearch(e));
            
            // Limpiar resultados cuando se borra el input
            searchInput.addEventListener('focus', () => this.handleInputFocus());
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
            this.showAlert('Por favor ingresa un término de búsqueda', 'warning');
            return;
        }
        
        await this.performSearch(searchTerm, language);
    }

    /**
     * Maneja la búsqueda en tiempo real con debounce
     */
    handleLiveSearch(event) {
        const searchTerm = event.target.value.trim();
        
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        if (searchTerm.length >= 3) {
            this.debounceTimer = setTimeout(() => {
                const language = document.getElementById('language').value;
                this.performSearch(searchTerm, language);
            }, 500);
        } else if (searchTerm.length === 0) {
            this.clearResults();
        }
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

            // --- Detectar si la búsqueda es SEMÁNTICA ---
            const isSemantic =
                lower.includes("actuo") ||
                lower.includes("actor") ||
                lower.includes("actriz") ||
                lower.includes("dirig") ||
                lower.includes("películas de") ||
                lower.includes("en que pelicula") ||
                lower.includes("pelicula de") ||
                lower.includes("director") ||
                lower.includes("año") ||
                lower.includes("estrenada") ||
                lower.match(/(19|20)\d{2}/); // detectar año

            let url = "";

            if (isSemantic) {
                //BÚSQUEDA SEMÁNTICA
                url = `/api/semantic_search?q=${encodeURIComponent(term)}&lang=${language}`;
                console.log("➡ Usando búsqueda SEMÁNTICA:", url);
            } else {
                //BÚSQUEDA NORMAL
                url = `/api/search?term=${encodeURIComponent(term)}&lang=${language}`;
                console.log("➡ Usando búsqueda NORMAL:", url);
            }

            // --- Ejecutar petición ---
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // --- Unificar resultados ---
            if (isSemantic) {
                this.currentResults = {
                    local: data.local || [],
                    external: data.external || [],
                    all: [...(data.local || []), ...(data.external || [])]
                };
            } else {
                this.currentResults = {
                    local: data.local || [],
                    external: data.external || [],
                    all: [...(data.local || []), ...(data.external || [])]
                };
            }

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
        
        // Actualizar contadores en las pestañas
        this.updateTabCounts();
        
        // Mostrar resultados en cada pestaña
        this.renderMovieResults('allResults', this.currentResults.all);
        this.renderMovieResults('localResults', this.currentResults.local);
        this.renderMovieResults('externalResults', this.currentResults.external);
        
        // Mostrar la sección de resultados
        resultsSection?.classList.remove('d-none');
        noResults?.classList.add('d-none');
        this.hideError();
    }

    /**
     * Actualiza los contadores en las pestañas
     */
    updateTabCounts() {
        const allCount = document.getElementById('allCount');
        const localCount = document.getElementById('localCount');
        const externalCount = document.getElementById('externalCount');
        
        if (allCount) allCount.textContent = this.currentResults.all.length;
        if (localCount) localCount.textContent = this.currentResults.local.length;
        if (externalCount) externalCount.textContent = this.currentResults.external.length;
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
        
        // Añadir animación de aparición
        this.animateCards(container);
    }

    /**
     * Crea una tarjeta HTML para una película
     */
    createMovieCard(movie) {
        const sourceClass = movie.tipo === 'local' ? 'local' : 'external';
        const sourceText = movie.fuente || (movie.tipo === 'local' ? 'Ontología Local' : 'DBpedia');
        
        return `
            <div class="movie-card ${sourceClass}">
                <h3 class="movie-title">${this.escapeHtml(movie.titulo)}</h3>
                <div class="movie-director">
                    Director: ${this.escapeHtml(movie.director)}
                </div>
                <p class="movie-synopsis">${this.escapeHtml(movie.sinopsis)}</p>
                
                <div class="movie-details mb-2">
                    ${movie.anio ? `
                        <div class="detail-item">
                            <small class="text-muted">Año: ${this.escapeHtml(movie.anio)}</small>
                        </div>
                    ` : ''}
                    
                    ${movie.duracion ? `
                        <div class="detail-item">
                            <small class="text-muted">Duración: ${this.escapeHtml(movie.duracion)}</small>
                        </div>
                    ` : ''}
                    
                    ${movie.genero ? `
                        <div class="detail-item">
                            <small class="text-muted">Género: ${this.escapeHtml(movie.genero)}</small>
                        </div>
                    ` : ''}
                </div>
                
                <div class="movie-meta">
                    <span class="source-badge ${sourceClass}">
                        ${sourceText}
                    </span>
                    ${movie.uri ? `
                        <a href="${movie.uri}" target="_blank" class="btn btn-outline-secondary btn-sm">
                            Ver más
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }


    /**
     * Crea una tarjeta HTML para una persona
     */
    createPersonCard(person) {
        const sourceClass = person.tipo === 'local' ? 'local' : 'external';
        const sourceText = person.fuente || (person.tipo === 'local' ? 'Ontología Local' : 'DBpedia');

        return `
            <div class="person-card ${sourceClass}">
                
                <h3 class="person-name">${this.escapeHtml(person.nombre)}</h3>

                ${person.descripcion ? `
                    <p class="person-description">
                        ${this.escapeHtml(person.descripcion)}
                    </p>
                ` : ''}

                <div class="person-details mb-2">
                    
                    ${person.fechaNacimiento ? `
                        <div class="detail-item">
                            <small class="text-muted">
                                Fecha de nacimiento: ${this.escapeHtml(person.fechaNacimiento)}
                            </small>
                        </div>
                    ` : ''}

                    ${person.ocupacion ? `
                        <div class="detail-item">
                            <small class="text-muted">
                                Ocupación: ${this.escapeHtml(person.ocupacion)}
                            </small>
                        </div>
                    ` : ''}

                </div>

                <div class="person-meta">
                    <span class="source-badge ${sourceClass}">
                        ${sourceText}
                    </span>

                    ${person.uri ? `
                        <a href="${person.uri}" target="_blank" class="btn btn-outline-secondary btn-sm">
                            Ver más
                        </a>
                    ` : ''}
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
                title: 'Sin resultados locales',
                text: 'No se encontraron películas en tu ontología local.'
            },
            'externalResults': {
                title: 'Sin resultados de DBpedia',
                text: 'No se encontraron películas en DBpedia para esta búsqueda.'
            }
        };
        
        const config = messages[containerId] || {
            title: 'Sin resultados',
            text: 'No hay películas para mostrar.'
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
        this.currentResults = { local: [], external: [], all: [] };
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
        
        // Insertar en el contenedor de alertas o al principio del contenido
        const container = document.querySelector('.container') || document.body;
        const alertElement = document.createElement('div');
        alertElement.innerHTML = alertHtml;
        container.prepend(alertElement.firstElementChild);
        
        // Auto-remover después de 5 segundos
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
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Método de utilidad para logging
     */
    log(message, data = null) {
        console.log(`[CinemaSearch] ${message}`, data);
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.cinemaSearch = new CinemaSearch();
});

// Exportar para uso en módulos (opcional)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CinemaSearch;
}