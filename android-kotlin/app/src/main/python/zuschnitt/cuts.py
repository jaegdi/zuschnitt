"""Compute ordered guillotine cut lines from a sheet layout.

Algorithm – shortest-first guillotine sequencing:
  1. Start with the full sheet as the current region.
  2. Collect all cut positions that lie strictly inside this region.
     When a kerf creates two nearby boundaries, keep only the boundary
     closer to the reference point.
  3. A horizontal cut (parallel to X-axis) has length = region_width.
     A vertical cut (parallel to Y-axis) has length = region_height.
  4. Choose the cut whose length is shortest (fewest passes of the saw).
  5. That cut splits the region into two sub-regions; recurse on each.
  6. Cuts are numbered in the order they are chosen (pre-order).

Reference point: top-left corner of the sheet (x=0, y=0).
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import PlacedPiece2D, SheetLayout

_TOL = 0.5   # mm – tolerance for deduplication / boundary exclusion


def _collapse_kerf_edges(positions: set[float], kerf: float) -> list[float]:
    """Collapse paired kerf edges to the reference-side boundary only."""
    ordered = sorted(positions)
    if kerf <= _TOL:
        return ordered

    collapsed: list[float] = []
    for pos in ordered:
        if collapsed and pos - collapsed[-1] <= kerf + _TOL:
            continue
        collapsed.append(pos)
    return collapsed


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

    def area(self) -> float:
        return self.w * self.h


def _placement_in_region(pl: PlacedPiece2D, region: _Region) -> bool:
    return (
        pl.x >= region.x - _TOL
        and pl.y >= region.y - _TOL
        and pl.x + pl.placed_width <= region.x + region.w + _TOL
        and pl.y + pl.placed_height <= region.y + region.h + _TOL
    )


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def compute_cuts(layout: SheetLayout, kerf: float = 0.0) -> list[CutLine]:
    """Return cuts in shortest-first guillotine order."""
    sw, sh = layout.stock.width, layout.stock.height

    ordered: list[CutLine] = []
    counter = [0]

    def _split_horizontal(region: _Region, pos: float) -> tuple[_Region, _Region]:
        top = _Region(region.x, region.y, region.w, pos - region.y)
        bottom = _Region(region.x, pos, region.w, region.y + region.h - pos)
        return top, bottom

    def _split_vertical(region: _Region, pos: float) -> tuple[_Region, _Region]:
        left = _Region(region.x, region.y, pos - region.x, region.h)
        right = _Region(pos, region.y, region.x + region.w - pos, region.h)
        return left, right

    def _classify_horizontal(
        region: _Region,
        placements: list[PlacedPiece2D],
        y: float,
    ) -> tuple[list[PlacedPiece2D], list[PlacedPiece2D]] | None:
        top: list[PlacedPiece2D] = []
        bottom: list[PlacedPiece2D] = []
        for pl in placements:
            bottom_edge = pl.y + pl.placed_height
            if bottom_edge <= y + _TOL:
                top.append(pl)
            elif pl.y >= y - _TOL:
                bottom.append(pl)
            else:
                return None
        if not top and not bottom:
            return None
        return top, bottom

    def _classify_vertical(
        region: _Region,
        placements: list[PlacedPiece2D],
        x: float,
    ) -> tuple[list[PlacedPiece2D], list[PlacedPiece2D]] | None:
        left: list[PlacedPiece2D] = []
        right: list[PlacedPiece2D] = []
        for pl in placements:
            right_edge = pl.x + pl.placed_width
            if right_edge <= x + _TOL:
                left.append(pl)
            elif pl.x >= x - _TOL:
                right.append(pl)
            else:
                return None
        if not left and not right:
            return None
        return left, right

    def _sequence(region: _Region, placements: list[PlacedPiece2D]) -> None:
        if not placements:
            return

        h_candidates: set[float] = set()
        v_candidates: set[float] = set()
        for pl in placements:
            for ey in (pl.y, pl.y + pl.placed_height):
                if region.y + _TOL < ey < region.y + region.h - _TOL:
                    h_candidates.add(round(ey, 2))
            for ex in (pl.x, pl.x + pl.placed_width):
                if region.x + _TOL < ex < region.x + region.w - _TOL:
                    v_candidates.add(round(ex, 2))

        h_local = _collapse_kerf_edges(h_candidates, kerf)
        v_local = _collapse_kerf_edges(v_candidates, kerf)
        if kerf > _TOL:
            if region.y > _TOL:
                h_local = [y for y in h_local if y - region.y > kerf + _TOL]
            if region.y + region.h < sh - _TOL:
                h_local = [y for y in h_local if region.y + region.h - y > kerf + _TOL]
            if region.x > _TOL:
                v_local = [x for x in v_local if x - region.x > kerf + _TOL]
            if region.x + region.w < sw - _TOL:
                v_local = [x for x in v_local if region.x + region.w - x > kerf + _TOL]

        best_orient = None
        best_pos = 0.0
        best_key = (float("inf"), float("inf"), float("inf"), float("inf"))
        best_split: tuple[_Region, list[PlacedPiece2D], _Region, list[PlacedPiece2D]] | None = None

        for y in h_local:
            classified = _classify_horizontal(region, placements, y)
            if classified is None:
                continue
            top_placements, bottom_placements = classified
            top, bottom = _split_horizontal(region, y)
            detached = min(top.area(), bottom.area())
            edge_span = min(top.h, bottom.h)
            key = (region.w, detached, edge_span, y)
            if key < best_key:
                best_key = key
                best_orient = "H"
                best_pos = y
                best_split = (top, top_placements, bottom, bottom_placements)

        for x in v_local:
            classified = _classify_vertical(region, placements, x)
            if classified is None:
                continue
            left_placements, right_placements = classified
            left, right = _split_vertical(region, x)
            detached = min(left.area(), right.area())
            edge_span = min(left.w, right.w)
            key = (region.h, detached, edge_span, x)
            if key < best_key:
                best_key = key
                best_orient = "V"
                best_pos = x
                best_split = (left, left_placements, right, right_placements)

        if best_orient is None or best_split is None:
            return

        counter[0] += 1
        ordered.append(CutLine(number=counter[0], orientation=best_orient,
                               position=best_pos))

        first_region, first_placements, second_region, second_placements = best_split
        children = [
            (first_region, first_placements),
            (second_region, second_placements),
        ]
        children.sort(key=lambda child: (child[0].area(), child[0].y, child[0].x))
        _sequence(children[0][0], children[0][1])
        _sequence(children[1][0], children[1][1])

    root = _Region(0.0, 0.0, sw, sh)
    root_placements = [pl for pl in layout.placements if _placement_in_region(pl, root)]
    _sequence(root, root_placements)
    return ordered
