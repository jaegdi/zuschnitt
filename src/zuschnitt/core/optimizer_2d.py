"""2-D MAXRECTS bin-packing algorithm with kerf support."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .models import (
    StockSheet, Piece2D, PlacedPiece2D, SheetLayout,
)

# ---------------------------------------------------------------------------
# Internal rectangle helper
# ---------------------------------------------------------------------------

@dataclass
class _Rect:
    x: float
    y: float
    w: float
    h: float

    def area(self) -> float:
        return self.w * self.h

    def contains(self, other: "_Rect") -> bool:
        return (
            other.x >= self.x and other.y >= self.y
            and other.x + other.w <= self.x + self.w
            and other.y + other.h <= self.y + self.h
        )


# ---------------------------------------------------------------------------
# MAXRECTS algorithm
# ---------------------------------------------------------------------------

class _MaxRects:
    """Single-bin MAXRECTS packer (Best Short Side Fits heuristic)."""

    def __init__(self, width: float, height: float, kerf: float) -> None:
        self.bin_w = width
        self.bin_h = height
        self.kerf = kerf
        self._free: list[_Rect] = [_Rect(0, 0, width, height)]
        self.placements: list[PlacedPiece2D] = []

    def insert(self, piece: Piece2D, allow_rotation: bool, prefer_rotated: bool = False) -> bool:
        """Try to insert piece. Returns True if placed."""
        best_rect: _Rect | None = None
        best_rotated = False
        best_score = float("inf")

        candidates = [(piece.width, piece.height, False)]
        if allow_rotation and not piece.grain_locked and piece.can_rotate:
            rotated = (piece.height, piece.width, True)
            candidates = [rotated, candidates[0]] if prefer_rotated else [candidates[0], rotated]

        for pw, ph, rotated in candidates:
            for free in self._free:
                # Reserve kerf space to the right/below unless piece sits at the sheet edge
                kw = self.kerf if free.x + pw < self.bin_w else 0
                kh = self.kerf if free.y + ph < self.bin_h else 0
                needed_w = pw + kw
                needed_h = ph + kh
                if needed_w <= free.w and needed_h <= free.h:
                    short = min(free.w - needed_w, free.h - needed_h)
                    if short < best_score:
                        best_score = short
                        best_rect = free
                        best_rotated = rotated

        if best_rect is None:
            return False

        pw = piece.height if best_rotated else piece.width
        ph = piece.width if best_rotated else piece.height

        placed = PlacedPiece2D(piece=piece, x=best_rect.x, y=best_rect.y, rotated=best_rotated)
        self.placements.append(placed)
        self._split(best_rect, pw, ph)
        self._prune()
        return True

    def _split(self, used: _Rect, pw: float, ph: float) -> None:
        """Split free rectangles around the newly placed piece (+ kerf)."""
        kw = self.kerf  # kerf to reserve to the right
        kh = self.kerf  # kerf to reserve below

        new_free: list[_Rect] = []
        for r in self._free:
            # check if the placed rectangle overlaps r
            px, py = used.x, used.y
            px2, py2 = px + pw + kw, py + ph + kh

            if not (px < r.x + r.w and px2 > r.x and py < r.y + r.h and py2 > r.y):
                new_free.append(r)
                continue

            # right of placed piece
            if r.x + r.w > px2:
                new_free.append(_Rect(px2, r.y, r.x + r.w - px2, r.h))
            # left of placed piece
            if r.x < px:
                new_free.append(_Rect(r.x, r.y, px - r.x, r.h))
            # below placed piece
            if r.y + r.h > py2:
                new_free.append(_Rect(r.x, py2, r.w, r.y + r.h - py2))
            # above placed piece
            if r.y < py:
                new_free.append(_Rect(r.x, r.y, r.w, py - r.y))

        self._free = new_free

    def _prune(self) -> None:
        """Remove free rectangles contained by another free rectangle."""
        to_remove = set()
        for i, a in enumerate(self._free):
            for j, b in enumerate(self._free):
                if i != j and j not in to_remove and b.contains(a):
                    to_remove.add(i)
                    break
        self._free = [r for i, r in enumerate(self._free) if i not in to_remove]


# ---------------------------------------------------------------------------
# Pre-orientation heuristic
# ---------------------------------------------------------------------------

_SIDE_MATCH_MIN_TOL = 5.0
_SIDE_MATCH_MAX_TOL = 15.0
_SIDE_MATCH_RATIO = 0.02


def _build_dimension_frequency(pieces: list[Piece2D]) -> Counter[float]:
    """Count candidate side lengths, weighted by piece quantity."""
    dim_freq: Counter[float] = Counter()
    for piece in pieces:
        dim_freq[piece.width] += piece.quantity
        if piece.can_rotate and not piece.grain_locked and piece.width != piece.height:
            dim_freq[piece.height] += piece.quantity
    return dim_freq


def _side_match_tolerance(side: float, kerf: float) -> float:
    scaled = abs(side) * _SIDE_MATCH_RATIO
    return max(kerf * 2, _SIDE_MATCH_MIN_TOL, min(scaled, _SIDE_MATCH_MAX_TOL))


def _shared_side_score(side: float, dim_freq: Counter[float], kerf: float) -> int:
    tol = _side_match_tolerance(side, kerf)
    return sum(weight for dim, weight in dim_freq.items() if abs(dim - side) <= tol)


def _preferred_rotation(piece: Piece2D, dim_freq: Counter[float], kerf: float) -> bool:
    """Return True when the rotated orientation aligns better with shared sides."""
    if not piece.can_rotate or piece.grain_locked or piece.width == piece.height:
        return False
    width_score = _shared_side_score(piece.width, dim_freq, kerf)
    height_score = _shared_side_score(piece.height, dim_freq, kerf)
    return height_score > width_score


def _preferred_side(piece: Piece2D, prefer_rotated: bool) -> float:
    return piece.height if prefer_rotated else piece.width


# ---------------------------------------------------------------------------
# Public optimizer function
# ---------------------------------------------------------------------------

def optimize_2d(
    sheets: list[StockSheet],
    pieces: list[Piece2D],
    kerf: float = 3.0,
    allow_rotation: bool = True,
) -> tuple[list[SheetLayout], list[Piece2D]]:
    """
    Pack pieces onto sheets using MAXRECTS.

    Returns:
        (layouts, unplaced_pieces)
    """
    # Expand each StockSheet by quantity
    stock_pool: list[StockSheet] = []
    for sheet in sheets:
        stock_pool.extend([sheet] * sheet.quantity)

    dim_freq: Counter[float] | None = None
    rotation_preference: dict[int, bool] = {}
    if allow_rotation:
        dim_freq = _build_dimension_frequency(pieces)
        rotation_preference = {
            id(piece): _preferred_rotation(piece, dim_freq, kerf)
            for piece in pieces
        }

    # Expand pieces by quantity and keep pieces with common sides adjacent.
    piece_list: list[Piece2D] = []
    for piece in pieces:
        piece_list.extend([piece] * piece.quantity)
    if dim_freq is None:
        piece_list.sort(key=lambda p: p.area(), reverse=True)
    else:
        piece_list.sort(
            key=lambda p: (
                -_shared_side_score(
                    _preferred_side(p, rotation_preference.get(id(p), False)),
                    dim_freq,
                    kerf,
                ),
                -_preferred_side(p, rotation_preference.get(id(p), False)),
                -p.area(),
            )
        )

    layouts: list[SheetLayout] = []
    remaining = list(piece_list)

    for stock in stock_pool:
        if not remaining:
            break
        packer = _MaxRects(stock.width, stock.height, kerf)
        still_remaining = []
        for piece in remaining:
            placed = packer.insert(
                piece,
                allow_rotation,
                prefer_rotated=rotation_preference.get(id(piece), False),
            )
            if not placed:
                still_remaining.append(piece)
        if packer.placements:
            layouts.append(SheetLayout(stock=stock, placements=packer.placements))
        remaining = still_remaining

    return layouts, remaining
