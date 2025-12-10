
LOCAL_NS = "http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#"

PROPERTY_MAPPING = {
    "nombre": "nombrePelicula",
    "sinopsis": "sinopsisPelicula",
    "duracion": "duracionPelicula",
    "anio": "fechaEstreno",
    "idioma": "lenguaje"   
}

RELATION_MAPPING = {
    "directores": {
        "local_class": "Director",
        "local_property": "dirigidaPor",
        "property_name": "nombrePersona"
    },
    "actores": {
        "local_class": "Actor",
        "local_property": "tieneActor",
        "property_name": "nombrePersona"
    },
    "generos": {
        "local_class": "Genero",
        "local_property": "tieneGenero",
        "property_name": "nombreGenero"
    },
    "organizacion": {
        "local_class": "Organizacion",
        "local_property": "estaAfiliadoA",
        "property_name": "nombreOrganizacion"
    }
}
