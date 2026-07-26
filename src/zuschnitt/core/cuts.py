"""Compute ordered guillotine cut lines from a sheet layout.

Each cut goes entirely across the sheet (or across the remaining piece
in the guillotine sequence).  We derive the minimum set of cut positions
from the piece-edge coordinates, then number them:
  1 … n   – horizontal cuts (across full width), sorted top → bottom
  n+1 … m – vertical cuts   (across full height), sorted left → right

A reference marker is placed at the top-left corner (0, 0).
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import SheetLayout

_TOL = 0.5  # mm tolerance for deduplication


@dataclass
class CutLine:
    number: int
    orientation: str   # "H" (horizontal) or "V" (vertical)
    position: float    # distance from reference: y for H cuts, x for V cuts


def compute_cuts(layout: SheetLayout) -> list[CutLine]:
    """Return ordered cut lines derived from piece placement edges."""
    sw, sh = layout.stock.width, layout.stock.height

    xs: set[float] = set()
    ys: set[float] = set()

    for pl in layout.placements:
        for ex in (pl.x, pl.x + pl.placed_width):
            if _TOL < ex < sw - _TOL:
                xs.add(round(ex, 2))
        for ey in (pl.y, pl.y + pl.placed_height):
            if _TOL < ey < sh - _TOL:
                ys.add(round(ey, 2))

    h_positions = sorted(ys)   # horizontal cuts: y positions, top→bottom
    v_positions = sorted(xs)   # vertical cuts:   x positions, left→right

    cuts: list[CutLine] = []
    for i, y in enumerate(h_positions, start=1):
        cuts.append(CutLine(number=i, orientation="H", position=y))
    offset = len(h_positions)
    for i, x in enumerate(v_positions, start=1):
        cuts.append(CutLine(number=offset + i, orientation="V", position=x))

    return cuts
