from __future__ import annotations

import json
from pathlib import Path

from backend.app import app


def main() -> None:
    target = Path(__file__).resolve().parent / "openapi.json"
    target.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print("Written OpenAPI schema to backend/openapi.json")


if __name__ == "__main__":
    main()
