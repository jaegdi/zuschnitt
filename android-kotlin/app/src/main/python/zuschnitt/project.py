"""JSON persistence for Zuschnitt projects (.zusc files)."""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    Project, Settings,
    StockSheet, StockBar,
    Piece2D, Piece1D,
)

_VERSION = 1


def save(project: Project, path: str | Path) -> None:
    path = Path(path)
    data = _project_to_dict(project)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load(path: str | Path) -> Project:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return _dict_to_project(data)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _project_to_dict(p: Project) -> dict:
    return {
        "version": _VERSION,
        "name": p.name,
        "mode": p.mode,
        "settings": {
            "kerf": p.settings.kerf,
            "unit": p.settings.unit,
            "allow_rotation": p.settings.allow_rotation,
            "grain_direction": p.settings.grain_direction,
        },
        "sheets": [
            {"width": s.width, "height": s.height, "quantity": s.quantity, "label": s.label}
            for s in p.sheets
        ],
        "pieces_2d": [
            {
                "width": pc.width, "height": pc.height, "quantity": pc.quantity,
                "label": pc.label, "can_rotate": pc.can_rotate,
                "grain_locked": pc.grain_locked, "color": pc.color,
            }
            for pc in p.pieces_2d
        ],
        "bars": [
            {"length": b.length, "quantity": b.quantity, "label": b.label}
            for b in p.bars
        ],
        "pieces_1d": [
            {"length": pc.length, "quantity": pc.quantity, "label": pc.label, "color": pc.color}
            for pc in p.pieces_1d
        ],
    }


def _dict_to_project(data: dict) -> Project:
    s = data.get("settings", {})
    settings = Settings(
        kerf=s.get("kerf", 3.0),
        unit=s.get("unit", "mm"),
        allow_rotation=s.get("allow_rotation", True),
        grain_direction=s.get("grain_direction", False),
    )
    return Project(
        name=data.get("name", "Untitled"),
        mode=data.get("mode", "2d"),
        settings=settings,
        sheets=[
            StockSheet(**sh) for sh in data.get("sheets", [])
        ],
        pieces_2d=[
            Piece2D(**pc) for pc in data.get("pieces_2d", [])
        ],
        bars=[
            StockBar(**b) for b in data.get("bars", [])
        ],
        pieces_1d=[
            Piece1D(**pc) for pc in data.get("pieces_1d", [])
        ],
    )
