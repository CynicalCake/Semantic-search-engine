# 🎬 CinemaSearch - Buscador Semántico de Películas

Un buscador avanzado de películas que combina ontologías locales con datos enlazados de DBpedia, utilizando tecnologías de Web Semántica.

## ✨ Características

- **🔍 Búsqueda Híbrida**: Combina datos de tu ontología local con información de DBpedia
- **📦 DBpedia Reducida**: Base de datos local con un subconjunto específico de películas de DBpedia
- **🌍 Multiidioma**: Soporte para español, inglés, francés y alemán
- **⚡ Interfaz Moderna**: Diseño responsivo con Bootstrap 5 y JavaScript ES6+
- **📊 Estadísticas en Tiempo Real**: Visualización de métricas de la ontología
- **🎨 Experiencia de Usuario Optimizada**: Búsqueda en tiempo real y animaciones fluidas

## 🎯 Nueva Característica: DBpedia Reducida

### ¿Qué es DBpedia Reducida?

DBpedia Reducida es una base de datos local que contiene un **subconjunto específico de películas descargado desde DBpedia**. Esta característica te proporciona:

- **📱 Acceso Offline**: Consulta datos de películas sin conexión a internet
- **⚡ Rapidez**: Búsquedas más rápidas que las consultas en línea a DBpedia
- **🔄 Actualización Periódica**: Los datos se actualizan automáticamente cada semana
- **🎬 Datos Curados**: Solo películas con información completa (director, año, etc.)

### Tres Fuentes de Datos

1. **🏠 Ontología Local**: Tus datos personalizados (verde)
2. **🌐 DBpedia Online**: Consultas en tiempo real (azul)
3. **💾 DBpedia Reducida**: Subconjunto local de DBpedia (morado)

## 🏗️ Arquitectura

### Backend (Python/Flask)
- **`app.py`**: Aplicación principal con endpoints REST
- **`config.py`**: Configuración centralizada
- **`services/`**: Servicios especializados
  - `ontology_service.py`: Manejo de la ontología local
  - `dbpedia_service.py`: Consultas a DBpedia
  - `dbpedia_reduced_service.py`: **NUEVO** - Manejo de DBpedia reducida

### Frontend
- **Templates Jinja2** con Bootstrap 5
- **JavaScript vanilla** para interactividad
- **CSS personalizado** con variables CSS y animaciones

### Datos
- **Ontología local**: Archivo OWL/OWX con datos estructurados
- **DBpedia Online**: Base de conocimiento enlazado externa
- **DBpedia Reducida**: Archivos locales (`dbpedia_reduced.ttl` y `dbpedia_reduced_metadata.json`)

## 🚀 Instalación

### Prerrequisitos
- Python 3.8+ 
- Entorno virtual (venv) activo

### Configuración del Entorno

```bash
# El entorno virtual ya está activo
pip install -r requirements.txt
```

### Estructura del Proyecto
```
Buscador/
├── app.py                 # Aplicación Flask principal
├── config.py             # Configuración
├── requirements.txt      # Dependencias Python
├── OntologiaPeliculasV5.owx  # Ontología local
├── services/             # Servicios backend
│   ├── __init__.py
│   ├── ontology_service.py
│   └── dbpedia_service.py
├── templates/            # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
└── static/              # Recursos estáticos
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## 💻 Uso

### Iniciar la Aplicación
```bash
python app.py
```

La aplicación estará disponible en: `http://127.0.0.1:5000`

### Funcionalidades Principales

#### 🔍 Búsqueda de Películas
1. **Búsqueda Simple**: Ingresa el título de una película
2. **Navegación por Pestañas**: 
   - **Todos**: Resultados combinados de las tres fuentes
   - **Local**: Solo resultados de tu ontología personal
   - **DBpedia**: Solo resultados de consultas online a DBpedia
   - **DBpedia Local**: Solo resultados de la base reducida local

### ⚙️ Gestión de DBpedia Reducida
- **Descarga Automática**: La primera vez que ejecutes la app, se descargarán ~2000 películas
- **Actualización Semanal**: Los datos se actualizan automáticamente
- **Expansión de Base**: Agrega más películas según tus necesidades
- **Estrategias de Descarga**:
  - Películas recientes (2000-2025)
  - Películas clásicas (1980-1999) 
  - Directores populares (Spielberg, Nolan, etc.)
  - Películas por género

#### 🎯 Tamaños Recomendados
- **Pequeña**: 500 películas (desarrollo/pruebas)
- **Mediana**: 2,000 películas (uso académico) ⭐ Recomendado
- **Grande**: 5,000 películas (aplicaciones de producción)
- **Completa**: 10,000+ películas (investigación)

#### 📱 Gestor de Base de Datos

```bash
# Ver estado actual
python manage_dbpedia.py status

# Configuración rápida a tamaño mediano
python manage_dbpedia.py setup mediana

# Expandir a 3000 películas
python manage_dbpedia.py expand 3000

# Actualizar completamente
python manage_dbpedia.py update

# Modo interactivo (recomendado)
python manage_dbpedia.py
```

#### 🧠 Búsqueda Semántica
Usa consultas en lenguaje natural como:
- "Películas dirigidas por Spielberg"
- "Filmes de acción del 2020"
- "Películas con Leonardo DiCaprio"

### Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Página principal |
| `/about` | GET | Información del proyecto |
| `/api/search` | GET | Búsqueda de películas |
| `/api/semantic_search` | GET | Búsqueda semántica |
| `/api/stats` | GET | Estadísticas de la ontología |
| `/api/health` | GET | Estado del servicio |
| `/api/reduced/stats` | GET | **NUEVO** - Estadísticas de DBpedia reducida |
| `/api/reduced/update` | POST | **NUEVO** - Forzar actualización |
| `/api/reduced/expand` | POST | **NUEVO** - Expandir base de datos |
| `/api/reduced/recommendations` | GET | **NUEVO** - Recomendaciones de tamaño |

### Parámetros de Búsqueda
- `term`: Término de búsqueda (requerido)
- `lang`: Idioma (es, en, fr, de) - por defecto: es
- `q`: Query en lenguaje natural para búsqueda semántica

### Prueba del Sistema

```bash
# Probar DBpedia Reducida
python test_dbpedia_reduced.py

# Gestionar la base de datos
python manage_dbpedia.py

# Probar endpoints de la aplicación
python test_endpoints.py
```

### Ejemplos de Expansión

```bash
# Configuración rápida para uso académico (2000 películas)
python manage_dbpedia.py setup mediana

# Para aplicaciones más robustas (5000 películas)
python manage_dbpedia.py setup grande

# Expansión personalizada
python manage_dbpedia.py expand 3500
```

## 🔧 Tecnologías Utilizadas

### Backend
- **Flask 3.1.2**: Framework web minimalista
- **RDFLib 7.4.0**: Procesamiento de ontologías RDF/OWL
- **SPARQLWrapper 2.0.0**: Consultas SPARQL a DBpedia

### Frontend
- **Bootstrap 5.3**: Framework CSS responsivo
- **Font Awesome 6.4**: Iconografía
- **Google Fonts (Poppins)**: Tipografía moderna
- **JavaScript ES6+**: Funcionalidad interactiva

### Datos Semánticos
- **SPARQL**: Lenguaje de consulta para RDF
- **OWL**: Ontología local de películas
- **DBpedia**: Base de conocimiento enlazado

## 📋 Funcionalidades Implementadas

### Requisitos del Proyecto
- ✅ **a)** Consultas a ontología local con SPARQL
- ✅ **b)** Integración con DBpedia como fuente externa
- ✅ **c)** Soporte multiidioma (ES, EN, FR, DE)
- ✅ **d)** Interfaz web intuitiva y moderna

### Características Adicionales
- 🔄 Búsqueda en tiempo real con debounce
- 📱 Diseño responsivo para móviles
- ⚡ Carga asíncrona de resultados
- 📊 Visualización de estadísticas
- 🎨 Animaciones CSS fluidas
- ⚠️ Manejo robusto de errores
- 📈 Health checks y monitoreo

## 🎯 Mejoras Implementadas

### Respecto al Código Original
1. **Separación de Responsabilidades**: Servicios especializados
2. **Arquitectura REST**: API endpoints bien definidos
3. **Interfaz Moderna**: Reemplazo de HTML inline por templates
4. **Manejo de Errores**: Páginas de error personalizadas
5. **Configuración Centralizada**: Archivo de configuración dedicado
6. **Logging Profesional**: Sistema de logs estructurado
7. **Validación de Datos**: Sanitización de inputs
8. **Optimización de Consultas**: SPARQL queries más eficientes

### Experiencia de Usuario
1. **Búsqueda Inteligente**: Sugerencias en tiempo real
2. **Navegación por Pestañas**: Organización clara de resultados
3. **Indicadores Visuales**: Diferenciación entre fuentes de datos
4. **Responsive Design**: Adaptación a dispositivos móviles
5. **Animaciones Suaves**: Feedback visual atractivo

## 🔍 Consultas SPARQL Implementadas

### Ontología Local
```sparql
PREFIX : <http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#>
SELECT DISTINCT ?titulo ?directorName ?sinopsis ?anio ?genero
WHERE {
    ?pelicula a :Pelicula .
    ?pelicula :nombrePelicula ?titulo .
    OPTIONAL { ?pelicula :dirigidaPor ?director . ?director :nombrePersona ?directorName }
    OPTIONAL { ?pelicula :sinopsisPelicula ?sinopsis }
    OPTIONAL { ?pelicula :anioEstreno ?anio }
    OPTIONAL { ?pelicula :genero ?genero }
    FILTER regex(?titulo, "término", "i")
}
```

### DBpedia
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?pelicula ?titulo ?directorName ?abstract ?releaseDate ?runtime
WHERE {
    ?pelicula a dbo:Film ;
             rdfs:label ?titulo .
    OPTIONAL { ?pelicula dbo:director ?director . ?director rdfs:label ?directorName }
    OPTIONAL { ?pelicula dbo:abstract ?abstract . FILTER(lang(?abstract) = "idioma") }
    OPTIONAL { ?pelicula dbo:releaseDate ?releaseDate }
    OPTIONAL { ?pelicula dbo:runtime ?runtime }
    
    FILTER regex(?titulo, "término", "i")
    FILTER (lang(?titulo) = "idioma" || lang(?titulo) = "en")
}
```

## 🐛 Solución de Problemas

### Error de Ontología
Si la ontología no se carga:
1. Verificar que el archivo `OntologiaPeliculasV5.owx` existe
2. Comprobar la ruta en `config.py`
3. Revisar logs en consola

### Error de DBpedia
Si DBpedia no responde:
1. Verificar conectividad a internet
2. El servicio puede estar temporalmente no disponible
3. Los resultados locales seguirán funcionando

### Error de Dependencias
```bash
pip install --upgrade -r requirements.txt
```

## 👥 Desarrollo Académico

Este proyecto fue desarrollado como parte del curso de **Web Semánticas**, aplicando:
- Ingeniería del conocimiento
- Tecnologías de la web semántica
- Datos enlazados (Linked Data)
- Consultas SPARQL avanzadas

## 📝 Notas del Desarrollador

### Cambios Principales Realizados
- Refactorización completa del código original generado por IA
- Implementación de patrones de diseño profesionales
- Mejora significativa de la experiencia de usuario
- Optimización de rendimiento y escalabilidad

### Próximas Mejoras Sugeridas
- Cache de consultas DBpedia
- Búsqueda por directores y géneros
- Filtros avanzados de búsqueda
- Exportación de resultados
- Sistema de favoritos

---

**Desarrollado con ❤️ para Web Semánticas**