import re
from typing import Optional, Dict

class IntentService:

    # ──────────────────────────────────────────
    #        DICCIONARIOS DE PALABRAS CLAVE
    # ──────────────────────────────────────────
    ACTOR_KEYWORDS = [
        "actor", "actriz", "actuó", "actuo", "actua", "actuó en", "actuado por"
    ]

    DIRECTOR_KEYWORDS = [
        "director", "dirigió", "dirigio", "dirigida por", "directed"
    ]

    GENRE_KEYWORDS = [
        "género", "genre", "películas de", "tipo de películas"
    ]

    YEAR_KEYWORDS = [
        "año", "year", "estrenada en", "estreno", "películas del", "del año"
    ]

    # ──────────────────────────────────────────
    #              DETECCIÓN DE INTENCIÓN
    # ──────────────────────────────────────────
    def detect_intent(self, text: str) -> Dict:
        original = text
        text = text.lower()

        intents = {
            "movie_by_actor": False,
            "movie_by_director": False,
            "movie_by_genre": False,
            "movie_by_year": False,
        }

        # Detecta todas las intenciones relevantes
        if any(k in text for k in self.ACTOR_KEYWORDS):
            intents["movie_by_actor"] = True

        if any(k in text for k in self.DIRECTOR_KEYWORDS):
            intents["movie_by_director"] = True

        if any(k in text for k in self.GENRE_KEYWORDS):
            intents["movie_by_genre"] = True

        if any(k in text for k in self.YEAR_KEYWORDS):
            intents["movie_by_year"] = True

        return {
            "intents": intents,
            "query_text": original
        }

    # ──────────────────────────────────────────
    #           EXTRACCIÓN DE ENTIDADES
    # ──────────────────────────────────────────
    def detect_actor(self, text: str) -> Optional[str]:
        """
        Detecta nombres después de "actor" o "actriz".
        Ej: 'actor Brad Pitt' → 'Brad Pitt'
        """
        patterns = [
            r"actor\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3})",
            r"actu[oó]\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3})",
            r"actuado por\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3})",
            r"actriz\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3})"
        ]

        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()

        return None

    def detect_director(self, text: str) -> Optional[str]:
        """
        Detecta nombres después de 'director' o 'dirigida por'.
        """
        patterns = [
            r"director\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3})",
            r"dirigida por\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3})"
        ]

        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()

        return None

    def detect_year(self, text: str) -> Optional[int]:
        """
        Extrae un año como 1999, 2005, etc.
        """
        match = re.search(r"(19|20)\d{2}", text)
        return int(match.group()) if match else None

    def detect_genre(self, text: str) -> Optional[str]:
        """
        Extrae géneros del tipo 'películas de acción'.
        """
        m = re.search(r"pel[ií]culas de ([a-zA-ZñÑáéíóú]+)", text.lower())
        if m:
            return m.group(1)
        return None

