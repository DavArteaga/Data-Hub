"""Value normalisation utilities for DataCore Hub.

Responsible for cleaning and standardising raw scraped / imported data
before it is persisted as a Valor record.
"""
from __future__ import annotations

import re
from typing import Any


def normalize_nit(raw: str) -> str:
    """Strip spaces and ensure NIT has the dash format 'XXXXXXXXX-D'."""
    raw = raw.strip().replace(" ", "")
    # Already has a dash
    if "-" in raw:
        return raw
    # Last character is the check digit – insert dash
    if len(raw) >= 2:
        return f"{raw[:-1]}-{raw[-1]}"
    return raw


def normalize_numeric(raw: Any) -> tuple[str, float | None]:
    """Return (valor_str, valor_numerico) from an arbitrary raw value.

    Handles:
    - Plain numbers (int/float)
    - Strings with currency symbols, dots/commas as thousands separators
    """
    if raw is None:
        return ("", None)
    raw_str = str(raw).strip()
    # Remove currency symbols and spaces
    cleaned = re.sub(r"[$\s]", "", raw_str)
    # Colombian number format: periods as thousands, comma as decimal
    # e.g. "1.280.000.000" or "1,280,000,000"
    # Heuristic: if there are multiple separators remove them as thousands sep
    cleaned = cleaned.replace(".", "").replace(",", "")
    try:
        numeric = float(cleaned)
        return (raw_str, numeric)
    except ValueError:
        return (raw_str, None)


def normalize_estado(raw: str) -> str:
    mapping = {
        "activa": "Activa",
        "inactiva": "Inactiva",
        "liquidada": "Liquidada",
        "en liquidacion": "En Liquidación",
        "cancelada": "Cancelada",
    }
    return mapping.get(raw.strip().lower(), raw.strip().title())


def normalize_ciiu(raw: str) -> str:
    """Strip whitespace and uppercase the CIIU code."""
    return raw.strip().upper()
