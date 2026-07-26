"""
Bridge for calling the Zuschnitt optimizer from Kotlin/Android via Chaquopy.
"""

from zuschnitt.models import StockSheet, Piece2D, Settings
from zuschnitt.optimizer_2d import optimize_2d


def optimize_simple(sheets_data, pieces_data, kerf=3.0):
    """
    Simplified optimizer entry point for Android.

    Args:
        sheets_data: list of dicts with 'width', 'height', 'quantity' keys
        pieces_data: list of dicts with 'width', 'height', 'quantity' keys
        kerf: cut width in mm (default: 3.0)

    Returns:
        dict with 'success', 'layouts_count', 'unplaced_count', 'layouts' keys
    """
    try:
        sheets = [
            StockSheet(
                width=float(s["width"]),
                height=float(s["height"]),
                quantity=int(s.get("quantity", 1)),
            )
            for s in sheets_data
        ]

        pieces = [
            Piece2D(
                width=float(p["width"]),
                height=float(p["height"]),
                quantity=int(p.get("quantity", 1)),
                can_rotate=bool(p.get("can_rotate", True)),
            )
            for p in pieces_data
        ]

        layouts, unplaced = optimize_2d(sheets, pieces, kerf=kerf)

        result = {
            "success": len(unplaced) == 0,
            "layouts_count": len(layouts),
            "unplaced_count": len(unplaced),
            "total_waste": 0.0,
            "layouts": [],
        }

        for layout in layouts:
            used_area = sum(p.piece.area() for p in layout.placements)
            total_area = layout.stock.area()
            waste = total_area - used_area
            result["total_waste"] += waste
            result["layouts"].append({
                "sheet_width": layout.stock.width,
                "sheet_height": layout.stock.height,
                "pieces_count": len(layout.placements),
                "waste": waste,
                "efficiency": (used_area / total_area * 100) if total_area > 0 else 0.0,
            })

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}
