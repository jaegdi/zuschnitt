"""1-D cutting optimizer using First-Fit Decreasing (FFD)."""

from __future__ import annotations

from .models import StockBar, Piece1D, PlacedPiece1D, BarLayout


def optimize_1d(
    bars: list[StockBar],
    pieces: list[Piece1D],
    kerf: float = 3.0,
) -> tuple[list[BarLayout], list[Piece1D]]:
    """
    Pack linear pieces onto bars using First-Fit Decreasing.

    Returns:
        (layouts, unplaced_pieces)
    """
    # Expand stock pool
    stock_pool: list[StockBar] = []
    for bar in bars:
        stock_pool.extend([bar] * bar.quantity)

    # Expand and sort pieces (longest first)
    piece_list: list[Piece1D] = []
    for piece in pieces:
        piece_list.extend([piece] * piece.quantity)
    piece_list.sort(key=lambda p: p.length, reverse=True)

    # Track remaining capacity per bar
    layouts: list[BarLayout] = []
    remaining_caps: list[float] = []
    unplaced: list[Piece1D] = []

    for piece in piece_list:
        placed = False
        for i, layout in enumerate(layouts):
            cap = remaining_caps[i]
            if piece.length <= cap:
                offset = layout.stock.length - cap
                layout.placements.append(PlacedPiece1D(piece=piece, offset=offset))
                remaining_caps[i] -= piece.length + kerf
                placed = True
                break

        if not placed:
            if stock_pool:
                bar = stock_pool.pop(0)
                layout = BarLayout(stock=bar)
                layout.placements.append(PlacedPiece1D(piece=piece, offset=0.0))
                layouts.append(layout)
                remaining_caps.append(bar.length - piece.length - kerf)
            else:
                unplaced.append(piece)

    return layouts, unplaced
