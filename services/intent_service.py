from typing import Dict, List, Any
import re

class IntentService:

    ACTOR_KEYWORDS = [
        "actor", "actriz", "actuó", "actuo", "actua", "actuó en",
        "actuado por", "cast", "performed by", "acteur", "schauspieler"
    ]

    DIRECTOR_KEYWORDS = [
        "director", "dirigió", "dirigio", "dirigida por", "directed by",
        "réalisé par", "regie"
    ]

    GENRE_KEYWORDS = [
        "género", "genre", "películas de", "movies of", "films de",
        "filme de", "genre de film", "film genre"
    ]

    YEAR_KEYWORDS = [
        "año", "year", "estrenada en", "released in", "del año",
        "première en", "jahr"
    ]

    STUDIO_KEYWORDS = [
        "distribuido por", "producción de", "produced by", "distributed by",
        "studio", "empresa productora", "studio", "societe de production"
    ]

    def __init__(self, ner_service, tmdb_service=None):
        """
        ner_service: instancia de NERServicePRO
        tmdb_service: instancia de TMDBService para detectar roles automáticamente
        """
        self.ner = ner_service
        self.tmdb = tmdb_service

    # Detectar roles de personas con TMDB
    def detect_roles_from_tmdb(self, persons: List[str]) -> Dict[str, List[str]]:
        roles = {"actor": [], "director": []}
        if not self.tmdb:
            return roles
        for p in persons:
            role = self.tmdb.get_role(p)
            if role == "actor":
                roles["actor"].append(p)
            elif role == "director":
                roles["director"].append(p)
        return roles

    # Detectar intenciones y extraer entidades
    def detect_intent(self, text: str, lang: str) -> Dict[str, Any]:
        text_low = text.lower()
        entities = self.ner.extract_all(text, lang)

        persons = entities.get("persons", [])
        years = entities.get("years", [])
        genres = entities.get("genres", [])
        studios = entities.get("orgs", [])

        tmdb_roles = self.detect_roles_from_tmdb(persons)

        # Inicializar intenciones
        intents = {
            "movie_by_actor": False,
            "movie_by_director": False,
            "movie_by_genre": False,
            "movie_by_year": False,
            "movie_by_person": False,
            "movie_by_studio": False
        }

        # Detectar intenciones por palabras clave
        if any(k in text_low for k in self.ACTOR_KEYWORDS) or tmdb_roles["actor"]:
            intents["movie_by_actor"] = True
        if any(k in text_low for k in self.DIRECTOR_KEYWORDS) or tmdb_roles["director"]:
            intents["movie_by_director"] = True
        if any(k in text_low for k in self.GENRE_KEYWORDS) or genres:
            intents["movie_by_genre"] = True
        if any(k in text_low for k in self.YEAR_KEYWORDS) or years:
            intents["movie_by_year"] = True
        if persons and not (intents["movie_by_actor"] or intents["movie_by_director"]):
            intents["movie_by_person"] = True
        if any(k in text_low for k in self.STUDIO_KEYWORDS) or studios:
            intents["movie_by_studio"] = True

        return {
            "intents": intents,
            "persons": persons,
            "roles": tmdb_roles,
            "years": years,
            "genres": genres,
            "studios": studios
        }

    # Métodos auxiliares
    def detect_year(self, text: str) -> Any:
        match = re.search(r"(19|20)\d{2}", text)
        return int(match.group()) if match else None

    def detect_genre(self, text: str, lang: str = "en") -> Any:
        genres = self.ner.extract_genres(text, lang)
        return genres[0] if genres else None

    def _has_semantic_keywords(self, text: str, lang: str):
        t = text.lower()

        keywords = {
            "es": ["actor", "actriz", "actores", "reparto", "participaron", "dirigió", "director", "distribuido por"],
            "en": ["actor", "actress", "cast", "starring", "who acted", "directed"],
            "fr": ["acteur", "actrice", "distribution", "joué", "réalisé"],
            "de": ["schauspieler", "besetzung", "mitgespielt", "regisseur"]
        }

        for kw in keywords.get(lang, []):
            if kw in t:
                return True
        return False

    def detect_semantic_intent_multilingual(query, persons, movies, lang):
        q = query.lower()

        actor_words = ROLE_KEYWORDS["actor"].get(lang, [])
        director_words = ROLE_KEYWORDS["director"].get(lang, [])
        movie_words = MOVIE_WORDS.get(lang, [])

        # --- A. Actores de una película ---
        for aw in actor_words:
            for mw in movie_words:
                if aw in q and mw in q and movies:
                    return {
                        "intent": "actors_of_movie",
                        "movie": movies[0],
                        "person": None,
                        "role": "actor"
                    }

        # --- B. Películas de un actor ---
        for aw in actor_words:
            for p in persons:
                if aw in q and p.lower() in q:
                    return {
                        "intent": "movies_by_actor",
                        "movie": None,
                        "person": p,
                        "role": "actor"
                    }

        # --- C. fallback normal (tu lógica previa)
        return {
            "intent": None,
            "movie": movies[0] if movies else None,
            "person": persons[0] if persons else None
        }
