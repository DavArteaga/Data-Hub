"""Verificación de salud de los scrapers de DataCore Hub.

Corre cada scraper aislado contra los NITs sintéticos del seed y reporta:
  - estado (ok / warn / error)
  - número de registros devueltos
  - número de rechazos
  - mensaje (si aplica)
  - tiempo de ejecución

Adicionalmente prueba DatosGovScraper con NITs reales conocidos
(Bancolombia, Ecopetrol) como sanity check de que la integración API funciona.

Uso:
    python scripts/verify_scrapers.py

Salida: tabla legible + JSON con la matriz para consumo programático.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

# Permitir importar app.* cuando se ejecuta desde la raíz del backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.base import ScrapeResult
from app.scrapers.dane_scraper import DaneScraper
from app.scrapers.datos_gov_scraper import DatosGovScraper
from app.scrapers.mock_scraper import MockScraper
from app.scrapers.rues_scraper import RuesScraper
from app.scrapers.siis_scraper import SiisScraper


SEED_NITS = [
    "900111111-1",
    "900222222-2",
    "900333333-3",
    "900444444-4",
    "900555555-5",
    "900666666-6",
]

# NITs reales conocidos para sanity check del API de datos.gov.co
REAL_NITS = [
    "890903938-8",  # Bancolombia
    "899999068-1",  # Ecopetrol
    "830122566-1",  # Grupo Aval
]


async def run_one(label: str, coro) -> dict:
    print(f"\n>>> Probando {label}...", flush=True)
    t0 = time.perf_counter()
    try:
        result: ScrapeResult = await coro
        elapsed = time.perf_counter() - t0
        sample = result.records[0] if result.records else None
        row = {
            "scraper": label,
            "estado": result.estado,
            "registros": len(result.records),
            "rechazados": result.registros_rechazados,
            "mensaje": result.mensaje,
            "tiempo_s": round(elapsed, 2),
            "muestra": sample,
        }
        print(
            f"  estado={row['estado']:<5} registros={row['registros']:<5} "
            f"rechazados={row['rechazados']:<3} t={row['tiempo_s']}s "
            f"msg={row['mensaje']}"
        )
        return row
    except Exception as exc:  # noqa: BLE001
        elapsed = time.perf_counter() - t0
        row = {
            "scraper": label,
            "estado": "exception",
            "registros": 0,
            "rechazados": 0,
            "mensaje": f"{type(exc).__name__}: {exc}",
            "tiempo_s": round(elapsed, 2),
            "muestra": None,
        }
        print(
            f"  !! EXCEPTION {row['mensaje']} (t={row['tiempo_s']}s)"
        )
        return row


async def main() -> int:
    print("=" * 72)
    print("VERIFICACION DE SCRAPERS - DataCore Hub")
    print("=" * 72)
    print(f"NITs sinteticos del seed: {SEED_NITS}")
    print(f"NITs reales (sanity check datos.gov.co): {REAL_NITS}")

    rows: list[dict] = []

    # 1) MockScraper — debe funcionar siempre (lee CSV local)
    rows.append(await run_one(
        "MockScraper (CSV local)",
        MockScraper(fuente_nombre="RUES").fetch(),
    ))

    # 2) DatosGovScraper — sanity check con NITs reales primero
    rows.append(await run_one(
        "DatosGovScraper [NITs REALES]",
        DatosGovScraper(nits=REAL_NITS).fetch(),
    ))

    # 3) DatosGovScraper — con NITs del seed (esperado: warn / 0 registros)
    rows.append(await run_one(
        "DatosGovScraper [NITs seed]",
        DatosGovScraper(nits=SEED_NITS).fetch(),
    ))

    # 4) DaneScraper — descarga Excel
    rows.append(await run_one(
        "DaneScraper [NITs seed]",
        DaneScraper(nits=SEED_NITS).fetch(),
    ))

    # 5) RuesScraper — Playwright contra rues.org.co (lento — 1 NIT solo)
    rows.append(await run_one(
        "RuesScraper [1 NIT seed]",
        RuesScraper(nits=SEED_NITS[:1]).fetch(),
    ))

    # 6) SiisScraper — Playwright contra siis.ia.supersociedades.gov.co (1 NIT)
    rows.append(await run_one(
        "SiisScraper [1 NIT seed]",
        SiisScraper(nits=SEED_NITS[:1]).fetch(),
    ))

    print("\n" + "=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(f"{'Scraper':<40} {'Estado':<10} {'Recs':<6} {'Rech':<6} {'Tiempo':<8}")
    print("-" * 72)
    for r in rows:
        print(
            f"{r['scraper']:<40} {r['estado']:<10} "
            f"{r['registros']:<6} {r['rechazados']:<6} {r['tiempo_s']}s"
        )

    out_path = Path(__file__).resolve().parent.parent / "data" / "scraper_health.json"
    out_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    print(f"\nMatriz completa guardada en: {out_path}")

    # Exit code: 0 si ningún scraper levantó excepción no esperada
    has_exception = any(r["estado"] == "exception" for r in rows)
    return 1 if has_exception else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
