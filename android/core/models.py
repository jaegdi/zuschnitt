"""Data models for Zuschnitt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

@dataclass
class StockSheet:
    """A rectangular stock panel available for cutting."""
    width: float          # mm
    height: float         # mm
    quantity: int = 1
    label: str = ""

    def area(self) -> float:
        return self.width * self.height


@dataclass
class StockBar:
    """A linear stock item (rod, pipe, lumber) available for cutting."""
    length: float         # mm
    quantity: int = 1
    label: str = ""


@dataclass
class Piece2D:
    """A rectangular piece to be cut from a sheet."""
    width: float          # mm
    height: float         # mm
    quantity: int = 1
    label: str = ""
    can_rotate: bool = True
    grain_locked: bool = False   # if True, rotation is forbidden regardless of can_rotate
    color: Optional[str] = None  # CSS hex color, auto-assigned if None

    def area(self) -> float:
        return self.width * self.height


@dataclass
class Piece1D:
    """A linear piece to be cut from a bar."""
    length: float         # mm
    quantity: int = 1
    label: str = ""
    color: Optional[str] = None


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------

@dataclass
class PlacedPiece2D:
    """A piece placed on a sheet at a specific position."""
    piece: Piece2D
    x: float              # mm from left
    y: float              # mm from top
    rotated: bool = False

    @property
    def placed_width(self) -> float:
        return self.piece.height if self.rotated else self.piece.width

    @property
    def placed_height(self) -> float:
        return self.piece.width if self.rotated else self.piece.height


@dataclass
class SheetLayout:
    """One stock sheet with all placed pieces on it."""
    stock: StockSheet
    placements: list[PlacedPiece2D] = field(default_factory=list)

    def used_area(self) -> float:
        return sum(p.piece.area() for p in self.placements)

    def waste_area(self) -> float:
        return self.stock.area() - self.used_area()

    def waste_pct(self) -> float:
        a = self.stock.area()
        return 0.0 if a == 0 else (self.waste_area() / a) * 100.0


@dataclass
class PlacedPiece1D:
    """A linear piece placed on a bar at a specific offset."""
    piece: Piece1D
    offset: float         # mm from start


@dataclass
class BarLayout:
    """One stock bar with all placed cuts."""
    stock: StockBar
    placements: list[PlacedPiece1D] = field(default_factory=list)

    def used_length(self) -> float:
        return sum(p.piece.length for p in self.placements)

    def waste_length(self) -> float:
        return self.stock.length - self.used_length()

    def waste_pct(self) -> float:
        ln = self.stock.length
        return 0.0 if ln == 0 else (self.waste_length() / ln) * 100.0


# ---------------------------------------------------------------------------
# Top-level project model
# ---------------------------------------------------------------------------

@dataclass
class Settings:
    kerf: float = 3.0        # mm – saw blade thickness
    unit: str = "mm"         # "mm" | "cm" | "inch"
    allow_rotation: bool = True
    grain_direction: bool = False


@dataclass
class Project:
    name: str = "Untitled"
    mode: str = "2d"          # "2d" | "1d"
    settings: Settings = field(default_factory=Settings)

    # 2D
    sheets: list[StockSheet] = field(default_factory=list)
    pieces_2d: list[Piece2D] = field(default_factory=list)

    # 1D
    bars: list[StockBar] = field(default_factory=list)
    pieces_1d: list[Piece1D] = field(default_factory=list)

    # Results (not persisted – recalculated on load)
    sheet_layouts: list[SheetLayout] = field(default_factory=list)
    bar_layouts: list[BarLayout] = field(default_factory=list)
