"""Tests for the 2-D and 1-D optimizers."""

import pytest
from zuschnitt.core.models import StockSheet, Piece2D, StockBar, Piece1D
from zuschnitt.core.optimizer_2d import optimize_2d
from zuschnitt.core.optimizer_1d import optimize_1d


# ---------------------------------------------------------------------------
# 2-D optimizer
# ---------------------------------------------------------------------------

class TestOptimize2D:
    def test_single_exact_fit(self):
        sheets = [StockSheet(width=1000, height=500, quantity=1)]
        pieces = [Piece2D(width=1000, height=500, quantity=1, can_rotate=False)]
        layouts, unplaced = optimize_2d(sheets, pieces, kerf=0)
        assert len(layouts) == 1
        assert len(layouts[0].placements) == 1
        assert unplaced == []

    def test_overflow_goes_to_second_sheet(self):
        sheets = [StockSheet(width=500, height=500, quantity=2)]
        pieces = [Piece2D(width=500, height=500, quantity=2, can_rotate=False)]
        layouts, unplaced = optimize_2d(sheets, pieces, kerf=0)
        assert len(layouts) == 2
        assert unplaced == []

    def test_no_stock_leaves_unplaced(self):
        sheets = [StockSheet(width=500, height=500, quantity=1)]
        pieces = [Piece2D(width=500, height=500, quantity=2, can_rotate=False)]
        layouts, unplaced = optimize_2d(sheets, pieces, kerf=0)
        assert len(unplaced) == 1

    def test_rotation_allows_fit(self):
        sheets = [StockSheet(width=600, height=300, quantity=1)]
        # piece 300×600 fits rotated (600×300)
        pieces = [Piece2D(width=300, height=600, quantity=1, can_rotate=True)]
        layouts, unplaced = optimize_2d(sheets, pieces, kerf=0, allow_rotation=True)
        assert unplaced == []

    def test_kerf_reduces_usable_area(self):
        # 3 pieces of 490 mm on a 1000 mm wide, 500 mm sheet with 10 mm kerf
        # Total needed width: 490 + 10 + 490 + 10 + 490 = 1490 > 1000  → only 2 fit per row
        sheets = [StockSheet(width=1000, height=500, quantity=1)]
        pieces = [Piece2D(width=490, height=490, quantity=3, can_rotate=False)]
        layouts, unplaced = optimize_2d(sheets, pieces, kerf=10, allow_rotation=False)
        # At most 1 piece fits per 490×490 slot with 10mm kerf on a 1000×500 sheet
        total_placed = sum(len(l.placements) for l in layouts)
        assert total_placed <= 3

    def test_waste_calculation(self):
        sheets = [StockSheet(width=1000, height=1000, quantity=1)]
        pieces = [Piece2D(width=500, height=500, quantity=1, can_rotate=False)]
        layouts, _ = optimize_2d(sheets, pieces, kerf=0)
        layout = layouts[0]
        assert abs(layout.waste_pct() - 75.0) < 1e-6

    def test_grain_lock_prevents_rotation(self):
        sheets = [StockSheet(width=600, height=300, quantity=1)]
        # Without rotation this piece doesn't fit (300×600 on 600×300 sheet — needs rotation)
        pieces = [Piece2D(width=300, height=600, quantity=1, can_rotate=True, grain_locked=True)]
        layouts, unplaced = optimize_2d(sheets, pieces, kerf=0, allow_rotation=True)
        assert len(unplaced) == 1


# ---------------------------------------------------------------------------
# 1-D optimizer
# ---------------------------------------------------------------------------

class TestOptimize1D:
    def test_exact_fit(self):
        bars = [StockBar(length=1000, quantity=1)]
        pieces = [Piece1D(length=1000, quantity=1)]
        layouts, unplaced = optimize_1d(bars, pieces, kerf=0)
        assert len(layouts) == 1
        assert unplaced == []

    def test_multiple_pieces_on_one_bar(self):
        bars = [StockBar(length=1000, quantity=1)]
        pieces = [Piece1D(length=300, quantity=3)]
        layouts, unplaced = optimize_1d(bars, pieces, kerf=0)
        assert len(layouts) == 1
        assert len(layouts[0].placements) == 3
        assert unplaced == []

    def test_kerf_limits_pieces(self):
        bars = [StockBar(length=1000, quantity=1)]
        # 3 × 330 mm = 990 mm + 2 kerfs of 10 mm = 1010 mm > 1000 mm → only 2 fit
        pieces = [Piece1D(length=330, quantity=3)]
        layouts, unplaced = optimize_1d(bars, pieces, kerf=10)
        total_placed = sum(len(l.placements) for l in layouts)
        assert total_placed == 2
        assert len(unplaced) == 1

    def test_overflow_uses_second_bar(self):
        bars = [StockBar(length=500, quantity=2)]
        pieces = [Piece1D(length=500, quantity=2)]
        layouts, unplaced = optimize_1d(bars, pieces, kerf=0)
        assert len(layouts) == 2
        assert unplaced == []

    def test_no_stock_leaves_unplaced(self):
        bars = [StockBar(length=500, quantity=1)]
        pieces = [Piece1D(length=500, quantity=2)]
        layouts, unplaced = optimize_1d(bars, pieces, kerf=0)
        assert len(unplaced) == 1

    def test_waste_calculation(self):
        bars = [StockBar(length=1000, quantity=1)]
        pieces = [Piece1D(length=600, quantity=1)]
        layouts, _ = optimize_1d(bars, pieces, kerf=0)
        assert abs(layouts[0].waste_pct() - 40.0) < 1e-6
