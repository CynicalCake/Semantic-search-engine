# services/intent_service.py
import re
from typing import Optional, Dict

class IntentService:
    """
    Detecta la intención del usuario basada en palabras clave.
    Intenciones soportadas por ahora:
      - movie_by_actor
      - movie_by_director
      - movie_by_genre
      - movie_by_year
    """

    def detect_intent(self, text: str) -> Dict[str, Optional[str]]:
        original = text
        text = text.lower()

        intent = None
        target = None

        # --- Actor ---
        if any(k in text for k in ["actuó", "actuo", "acto", "actua", "actuó en", "actor", "actriz"]):
            intent = "movie_by_actor"

        # --- Director ---
        elif any(k in text for k in ["dirigió", "dirigio", "directed", "director", "dirigida por"]):
            intent = "movie_by_director"

        # --- Género ---
        elif any(k in text for k in ["películas de", "genre", "género", "tipo de películas"]):
            intent = "movie_by_genre"

        # --- Año ---
        elif any(k in text for k in ["año", "year", "estrenada en", "peliculas del", "estreno"]):
            intent = "movie_by_year"

        return {
            "intent": intent,
            "query_text": original
        }

    def detect_year(self, text: str) -> Optional[int]:
        """
        Extrae año si existe.
        """
        match = re.search(r"(19|20)\d{2}", text)
        return int(match.group()) if match else None

    def detect_genre(self, text: str) -> Optional[str]:
        """
        Extrae género basado en palabras que sigan a 'películas de ...'
        Ejemplo: 'películas de terror' → terror
        """
        m = re.search(r"películas de ([a-zA-ZñÑáéíóú]+)", text.lower())
        if m:
            return m.group(1)
        return None
