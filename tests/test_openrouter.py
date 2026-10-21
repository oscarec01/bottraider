"""Prueba OpenRouter usando la key guardada en BD (no hardcodear secretos)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.database import Database
from models.ai_provider import get_ai_provider


def main():
    db = Database()
    if db.get_setting("ai_provider") != "openrouter":
        print("ai_provider no es openrouter; configura Ajustes primero")
        return 1
    if not db.get_setting("openrouter_api_key"):
        print("Falta openrouter_api_key en BD")
        return 1

    prov = get_ai_provider(db)
    print("FACTORY", prov.get_name())
    text = prov.query(
        'Responde SOLO JSON: {"ok": true, "signal": "ESPERAR"}',
        timeout=60,
        format_json=True,
    )
    print("TEST_RESPONSE:", repr(text[:500] if text else text))
    return 0 if text else 1


if __name__ == "__main__":
    raise SystemExit(main())
