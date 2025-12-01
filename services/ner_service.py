import spacy
from typing import List, Dict

class NERService:
    """
    Servicio de NLP para extraer entidades (actores, directores, etc.).
    Por ahora solo PERSON, pero puedes agregar más adelante.
    """

    def __init__(self, model: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model)
        except OSError:
            raise RuntimeError(
                f"El modelo {model} no está instalado. "
                f"Corre: python -m spacy download {model}"
            )

    def extract_persons(self, text: str) -> List[str]:
        """
        Extrae entidades de tipo PERSON del texto.
        Ejemplo: "En qué películas actuó Johnny Depp" → ["Johnny Depp"]
        """
        doc = self.nlp(text)
        persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        return list(set(persons))  # elimina duplicados

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Método más general por si luego agregas organización, lugares, etc.
        """
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            entities.setdefault(ent.label_, []).append(ent.text)
        return entities
