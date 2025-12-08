# ner_service.py
import re
from typing import List, Dict, Any
import spacy
from spacy.lang.en import English
from spacy.lang.es import Spanish
from spacy.lang.fr import French
from spacy.lang.de import German
from spacy.pipeline import EntityRuler

class NERService:

    YEAR_REGEX = re.compile(r"\b(19|20)\d{2}\b")

    # ——— Diccionarios iniciales (puedes ampliar) ———
    GENRES = {
        "en": [
            "action", "comedy", "drama", "horror", "thriller", "romance",
            "science fiction", "sci[- ]?fi", "fantasy", "animation", "documentary",
            "crime", "mystery", "adventure", "family"
        ],
        "es": [
            "acción", "comedia", "drama", "terror", "thriller", "romance",
            "ciencia ficción", "cienciaficción", "fantasía", "animación", "documental",
            "crimen", "misterio", "aventura", "familiar"
        ],
        "fr": [
            "action", "comédie", "drame", "horreur", "thriller", "romance",
            "science[- ]?fiction", "fantastique", "animation", "documentaire",
            "crime", "mystère", "aventure", "familial"
        ],
        "de": [
            "action", "komödie", "drama", "horror", "thriller", "romantik",
            "science[- ]?fiction", "fantasy", "animation", "dokumentation",
            "krimi", "mysterium", "abenteuer", "familie"
        ]
    }

    STUDIOS = {
        # lista pequeña inicial — amplía cuando lo necesites
        "en": ["Disney", "Walt Disney", "Warner Bros", "Warner Bros.", "Universal", "Paramount", "Netflix", "Amazon", "Pixar", "Marvel", "Lucasfilm", "20th Century Fox", "Sony Pictures"],
        "es": ["Disney", "Warner Bros", "Universal", "Paramount", "Netflix", "Amazon", "Pixar", "Marvel", "Lucasfilm", "Fox", "Sony"],
        "fr": ["Disney", "Warner Bros", "Universal", "Paramount", "Netflix", "Amazon", "Pixar", "Marvel", "Lucasfilm", "Fox", "Sony"],
        "de": ["Disney", "Warner Bros", "Universal", "Paramount", "Netflix", "Amazon", "Pixar", "Marvel", "Lucasfilm", "Fox", "Sony"]
    }

    SUPPORTED_LANGS = ["es", "en", "fr", "de"]

    def __init__(self, prefer_small_models: bool = True):
        """
        prefer_small_models: si True, intenta cargar los modelos '..._sm'. Si no están,
        hace fallback a 'xx_ent_wiki_sm' (multilingüe).
        """
        self.nlps = {}
        self.rulers = {}

        # intentamos cargar modelos por idioma; si no hay, fallback a xx_ent_wiki_sm
        for lang in self.SUPPORTED_LANGS:
            model_name = self._select_model_name(lang, prefer_small_models)
            try:
                self.nlps[lang] = spacy.load(model_name)
            except OSError:
                # fallback: modelo multilingüe
                try:
                    self.nlps[lang] = spacy.load("xx_ent_wiki_sm")
                except OSError:
                    raise RuntimeError(
                        "No se encontró ningún modelo spaCy para procesamiento. "
                        "Instala alguno de: es_core_news_sm, en_core_web_sm, fr_core_news_sm, de_core_news_sm "
                        "o xx_ent_wiki_sm"
                    )

            # Añadir EntityRuler con patrones de géneros y estudios
            ruler = self._build_ruler_for_lang(lang)
            # evitar duplicados si ya existe
            if "entity_ruler" not in [pipe[0] for pipe in self.nlps[lang].pipeline]:
                self.nlps[lang].add_pipe(ruler, name="entity_ruler", before="ner")
            self.rulers[lang] = ruler

    def _select_model_name(self, lang: str, small: bool = True) -> str:
        if lang == "es":
            return "es_core_news_md"
        if lang == "en":
            return "en_core_web_md"
        if lang == "fr":
            return "fr_core_news_md"
        if lang == "de":
            return "de_core_news_sm"
        return "xx_ent_wiki_sm"

    def _build_ruler_for_lang(self, lang: str):
        nlp = self.nlps[lang]

        # Construir patrones
        patterns = []
        for g in self.GENRES.get(lang, []):
            patterns.append({"label": "GENRE", "pattern": g})
        for s in self.STUDIOS.get(lang, []):
            patterns.append({"label": "STUDIO", "pattern": s})

        # Añadir EntityRuler correctamente en spaCy 3.x
        ruler = nlp.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": False})
        ruler.add_patterns(patterns)

    # -----------------------
    # Métodos públicos
    # -----------------------

    def _normalize_lang(self, lang: str) -> str:
        if not lang:
            return "en"
        lang = lang.lower()[:2]
        return lang if lang in self.SUPPORTED_LANGS else "en"

    def extract_persons(self, text: str, lang: str = "en") -> List[str]:
        nlp = self.nlps[self._normalize_lang(lang)]
        doc = nlp(text)
        persons = []
        seen = set()
        for ent in doc.ents:
            label = ent.label_.upper()
            if label in ("PERSON", "PER") and ent.text not in seen:
                persons.append(ent.text)
                seen.add(ent.text)
        return persons

    def extract_years(self, text: str) -> List[str]:
        """Extrae todos los años tipo 1999, 2005, 2010."""
        return list({m.group(0) for m in self.YEAR_REGEX.finditer(text)})

    def extract_genres(self, text: str, lang: str = "en") -> List[str]:
        nlp = self.nlps[self._normalize_lang(lang)]
        doc = nlp(text)
        found = []
        seen = set()
        for ent in doc.ents:
            if ent.label_ == "GENRE" and ent.text.lower() not in seen:
                found.append(ent.text)
                seen.add(ent.text.lower())
        # También hacer fallback con regex simple sobre diccionario
        if not found:
            for pattern in self.GENRES.get(self._normalize_lang(lang), []):
                if re.search(pattern, text, flags=re.IGNORECASE):
                    if pattern not in found:
                        found.append(pattern)
        return found

    def extract_orgs(self, text: str, lang: str = "en") -> List[str]:
        """Extrae ORG (productoras, distribuidoras, estudios) y STUDIO desde ruler."""
        nlp = self.nlps[self._normalize_lang(lang)]
        doc = nlp(text)
        orgs = []
        seen = set()
        for ent in doc.ents:
            lab = ent.label_.upper()
            if lab in ("ORG", "STUDIO") and ent.text not in seen:
                orgs.append(ent.text)
                seen.add(ent.text)
        return orgs

    def extract_places(self, text: str, lang: str = "en") -> List[str]:
        nlp = self.nlps[self._normalize_lang(lang)]
        doc = nlp(text)
        places = []
        seen = set()
        for ent in doc.ents:
            if ent.label_.upper() in ("GPE", "LOC") and ent.text not in seen:
                places.append(ent.text)
                seen.add(ent.text)
        return places

    def extract_all(self, text: str, lang: str = "en") -> Dict[str, Any]:
        """
        Extrae y devuelve un dict con:
          - persons: [..]
          - years: [..]
          - genres: [..]
          - orgs (studios/distributors): [..]
          - places: [..]
          - raw_entities: lista de (text, label)
        """
        nlang = self._normalize_lang(lang)
        nlp = self.nlps[nlang]
        doc = nlp(text)

        raw_entities = []
        for ent in doc.ents:
            raw_entities.append({"text": ent.text, "label": ent.label_})

        result = {
            "persons": self.extract_persons(text, nlang),
            "years": self.extract_years(text),
            "genres": self.extract_genres(text, nlang),
            "orgs": self.extract_orgs(text, nlang),
            "places": self.extract_places(text, nlang),
            "raw_entities": raw_entities
        }

        # heurística: si hay ORG pero no persons, a veces el usuario escribió el estudio -> propagarlo
        # (no obligatorio; solo ejemplo de cómo se puede mejorar)
        return result

