import requests
import re

class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_person(self, name: str):
        """Busca a una persona y devuelve su información."""
        url = f"{self.BASE_URL}/search/person"
        params = {
            "api_key": self.api_key,
            "query": name,
            "include_adult": False
        }
        resp = requests.get(url, params=params)

        if resp.status_code != 200:
            return None

        data = resp.json().get("results", [])
        if not data:
            return None
        
        return data[0]

    def get_role(self, name: str) -> str:
        """Devuelve 'actor', 'director' o None automáticamente."""
        person = self.search_person(name)
        if not person:
            return None
        
        dep = person.get("known_for_department", "").lower()

        if dep == "acting":
            return "actor"
        if dep == "directing":
            return "director"
        
        return None

    def search_movie_by_title(self, title_ini: str, language: str) -> dict:
        """
        Busca una película en TMDB por título y devuelve info básica:
        título localizado, poster, release_date
        """
        title_safe = re.sub(r"\s*\(.*?\)\s*", "", title_ini)
        title = title_safe.strip()
        if language=="es":
            language_tmdb="es-MX"
        else:
            language_tmdb=language

        try:
            url = f"{self.BASE_URL}/search/movie"
            params = {
                "api_key": self.api_key,
                "query": title,
                "language": language_tmdb,
                "include_adult": False,
                "page": 1
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return {}

            data = response.json()
            results = data.get("results", [])
            if not results:
                return {}

            # Tomamos la primera coincidencia
            movie = results[0]
            print (movie.get("title"), movie.get("poster_path"))
            return {
                "title": movie.get("title"),
                "poster_path": movie.get("poster_path"),
                "release_date": movie.get("release_date")
            }

        except Exception as e:
            print(f"Error buscando película en TMDB: {e}")
            return {}