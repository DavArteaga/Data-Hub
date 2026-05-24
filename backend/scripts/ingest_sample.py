"""Trigger a sample ingestion run via the ETL pipeline.

Run from the backend/ directory:
    python scripts/ingest_sample.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal, init_db
from app.etl.pipeline import run_ingestion

FUENTES = [
    "RUES",
    "Cámara de Comercio",
    "Superintendencia de Sociedades",
    "DIAN",
    "DANE",
]


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        for fuente in FUENTES:
            print(f"Ingesting {fuente}...")
            result = await run_ingestion(session, fuente)
            print(
                f"  estado={result['estado']} "
                f"ingestados={result['registros_ingestados']} "
                f"rechazados={result['registros_rechazados']}"
            )
            if result.get("mensaje"):
                print(f"  mensaje: {result['mensaje']}")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
