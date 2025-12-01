import spacy
from typing import List, Dict

class NERService:
    def __init__(self, model: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model)
        except OSError:
            raise RuntimeError(
                f"El modelo {model} no está instalado. "
                f"Corre: python -m spacy download {model}"
            )

    def extract_persons(self, text: str) -> List[str]:
        doc = self.nlp(text)
        seen = set()
        persons = []
        for ent in doc.ents:
            if ent.label_ == "PERSON" and ent.text not in seen:
                persons.append(ent.text)
                seen.add(ent.text)
        return persons
        
    def match_entity_after_keyword(self, text: str, keyword: str, entities: List[str]):
        text_low = text.lower()

        for ent in entities:
            pos_keyword = text_low.find(keyword)
            pos_ent = text.find(ent)

            if pos_keyword != -1 and pos_ent != -1 and pos_ent > pos_keyword:
                return ent

        return None

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            entities.setdefault(ent.label_, []).append(ent.text)
        return entities
