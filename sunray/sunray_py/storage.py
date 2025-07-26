import json
import os
from typing import Any, Dict, Optional

class Storage:
    """
    Persistentes Speichern und Laden von Roboterzustand.
    Portiert aus Storage.cpp/Storage.h.
    Verwendung:
      storage = Storage('state.json')
      success = storage.save(state_dict)
      state = storage.load()
    """
    def __init__(self, filename: str = 'state.json'):
        self.filename = filename

    def save(self, state: Dict[str, Any]) -> bool:
        """
        Speichert ein Dictionary als JSON-Datei.
        state: Schlüssel-Wert-Paare des zu speichernden Zustands.
        """
        try:
            with open(self.filename, 'w') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception:
            return False

    def load(self) -> Dict[str, Any]:
        """
        Lädt JSON-Datei und gibt Dictionary zurück.
        Gibt leeres Dict zurück, wenn Datei nicht existiert oder Fehler.
        """
        if not os.path.exists(self.filename):
            return {}
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
