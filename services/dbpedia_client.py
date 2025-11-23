# dbpedia_client.py
from SPARQLWrapper import SPARQLWrapper, JSON

def get_movies_from_dbpedia():

    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery(f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?movie ?label ?director ?actor ?releaseDate ?description ?duracionPelicula
        WHERE {{
            ?movie a dbo:Film .
            ?movie rdfs:label ?label .
            FILTER(lang(?label)="en")

            OPTIONAL {{ ?movie dbo:director ?director . }}
            OPTIONAL {{ ?movie dbo:starring ?actor . }}
            OPTIONAL {{ ?movie dbo:releaseDate ?releaseDate . }}
            OPTIONAL {{ ?movie dbo:runtime ?duracionPelicula . }}
            OPTIONAL {{ ?movie dbo:abstract ?description . FILTER(lang(?description)="en") }}
        }}
        LIMIT 10000
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    movies = []

    for row in results["results"]["bindings"]:
        movie = {}

        movie["rdfs:label"] = row["label"]["value"]
        movie["dbo:description"] = row.get("description", {}).get("value", "Sin descripción")
        movie["dbo:releaseDate"] = row.get("releaseDate", {}).get("value", "Desconocido")
        movie["dbo:runtime"] = row.get("duracionPelicula", {}).get("value", "Desconocido")

        # Director
        if "director" in row:
            movie["dbo:director"] = []
            uri = row["director"]["value"]
            movie["dbo:director"].append({
                "uri": uri,
                "nombre": uri.split("/")[-1].replace("_", " "),
                "birthDate": "Desconocido",
                "gender": "Desconocido"
            })

        # Actor
        if "actor" in row:
            movie["dbo:starring"] = []
            uri = row["actor"]["value"]
            movie["dbo:starring"].append({
                "uri": uri,
                "nombre": uri.split("/")[-1].replace("_", " "),
                "birthDate": "Desconocido",
                "gender": "Desconocido"
            })

        print("DEBUG DBPEDIA MOVIE:", movie)
        movies.append(movie)

    return movies
