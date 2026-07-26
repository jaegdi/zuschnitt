"""Compute ordered guillotine cut lines from a sheet layout.

Algorithm – shortest-first guillotine sequencing:
  1. Start with the full sheet as the current region.
  2. Collect all cut positions that lie strictly inside this region.
  3. A horizontal cut (parallel to X-axis) has length = region_width.
     A vertical cut (parallel to Y-axis) has length = region_height.
  4. Choose the cut whose length is shortest (fewest passes of the saw).
  5. That cut splits the region into two sub-regions; recurse on each.
  6. Cuts are numbered in the order they are chosen (pre-order).

Reference point: top-left corner of the sheet (x=0, y=0).
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import SheetLayout

_TOL = 0.5   # mm – tolerance for deduplication / boundary exclusion


@dataclass
class CutLine:
    number: int
    orientation: str   # "H" (horizontal across full region width)
                       # "V" (vertical across full region height)
    position: float    # absolute sheet coordinate: y for H, x for V


# ---------------------------------------------------------------------------
# Internal region type
# ---------------------------------------------------------------------------

class _Region:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x: float, y: float, w: float, h: float) -> None:
        self.x, self.y, self.w, self.h = x, y, w, h


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def compute_cuts(layout: SheetLayout) -> list[CutLine]:
    """Return cuts in shortest-first guillotine order."""
    sw, sh = layout.stock.width, layout.stock.height

    # Collect all unique interior cut positions
    h_all: set[float] = set()   # y-positions of horizontal cuts
    v_all: set[float] = set()   # x-positions of vertical cuts

    for pl in layout.placements:
        for ey in (pl.y, pl.y + pl.placed_height):
            if _TOL < ey < sh - _TOL:
                h_all.add(round(ey, 2))
        for ex in (pl.x, pl.x + pl.placed_width):
            if _TOL < ex < sw - _TOL:
                v_all.add(round(ex, 2))

    ordered: list[CutLine] = []
    counter = [0]

    def _sequence(region: _Region) -> None:
        # Cuts that lie strictly inside this region
        h_local = sorted(y for y in h_all if region.y + _TOL < y < region.y + region.h - _TOL)
        v_local = sorted(x for x in v_all if region.x + _TOL < x < region.x + region.w - _TOL)

        if not h_local and not v_local:
            return

        # Each horizontal cut spans region_width; vertical spans region_height.
        # Pick the shortest.
        best_orient = None
        best_pos = 0.0
        best_len = float("inf")

        for y in h_local:
            if region.w < best_len:
                best_len = region.w
                best_orient = "H"
                best_pos = y

        for x in v_local:
            if region.h < best_len:
                best_len = region.h
                best_orient = "V"
                best_pos = x

        counter[0] += 1
        ordered.append(CutLine(number=counter[0], orientation=best_orient,
                               position=best_pos))

        if best_orient == "H":
            top = _Region(region.x, region.y, region.w, best_pos - region.y)
            bot = _Region(region.x, best_pos, region.w,
                          region.y + region.h - best_pos)
            _sequence(top)
            _sequence(bot)
        else:
            lft = _Region(region.x, region.y, best_pos - region.x, region.h)
            rgt = _Region(best_pos, region.y,
                          region.x + region.w - best_pos, region.h)
            _sequence(lft)
            _sequence(rgt)

    _sequence(_Region(0.0, 0.0, sw, sh))
    return ordered
