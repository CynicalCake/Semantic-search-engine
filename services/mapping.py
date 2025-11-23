# -----------------------------------------
# Mapeos entre DBpedia y tu ontología local
# -----------------------------------------

# Namespace local (se usa en ontology_service)
LOCAL_NS = "http://www.semanticweb.org/anghely/ontologies/2025/8/OntologiaPeliculas#"

# -----------------------------------------
# 1) MAPEOS DE PROPIEDADES SIMPLES
# -----------------------------------------
# Traducción: propiedad DBpedia → propiedad local
PROPERTY_MAPPING = {
    "rdfs:label": "nombrePelicula",
    "dbo:description": "sinopsisPelicula",
    "dbo:runtime": "duracionPelicula",
    "dbp:country" : "paisPelicula",
    "dbp:language" : "idiomaPelicula",
    "dbo:budget" : "presupuestoPelicula",
    "dbo:releaseDate" : "fechaEstreno"
}

# -----------------------------------------
# 2) MAPEOS DE RELACIONES (objeto → objeto)
# -----------------------------------------
# Para tratar relaciones donde DBpedia devuelve un recurso,
# y tu ontología necesita crear individuos de otra clase.
RELATION_MAPPING = {
    "dbo:director": {
        "local_class": "Director",
        "properties": {
            "nombrePersona": "nombre",      # propiedad para el nombre
            "edadPersona": "dbo:birthDate", # fecha de nacimiento
            "generoPersona": "dbo:gender",             # si quieres traer género
        },
        "local_property": "dirigidaPor"       # relación desde la película
    },
    "dbo:starring": {
        "local_class": "Actor",
        "properties": {
            "nombrePersona": "nombre",      # propiedad para el nombre
            "edadPersona": "dbo:birthDate", # fecha de nacimiento
            "generoPersona": "dbo:gender",             # si quieres traer género
        },
        "local_property": "tieneActor"       # relación desde la película
    },
    "dbo:distributor": {
        "local_class": "Distribuidor",
        "properties": {
            "nombreOrganizacion": "nombre",
        },
        "local_property": "esDistribuidaPor"
    }
}

