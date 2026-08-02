"""
Bridge for calling the Zuschnitt optimizer from Kotlin/Android via Chaquopy.
"""

import json

from zuschnitt.models import StockSheet, Piece2D
from zuschnitt.cuts import compute_cuts
from zuschnitt.optimizer_2d import optimize_2d


def optimize_simple_json(sheets_json: str, pieces_json: str, kerf: float = 3.0) -> str:
    """
    JSON-in / JSON-out entry point called by Kotlin via Chaquopy.

    Using JSON strings avoids Chaquopy's unreliable auto-conversion of
    Kotlin List<Map<String,Any>> to Python dicts.

    Args:
        sheets_json: JSON array string, e.g. '[{"width":2440,"height":1220,"quantity":1}]'
        pieces_json: JSON array string, e.g. '[{"width":400,"height":300,"quantity":2}]'
        kerf: cut width in mm

    Returns:
        JSON string with keys: success, layouts_count, unplaced_count, total_waste, layouts
    """
    try:
        sheets_data = json.loads(sheets_json)
        pieces_data = json.loads(pieces_json)

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

        layouts, unplaced = optimize_2d(sheets, pieces, kerf=float(kerf))

        result = {
            "success": len(unplaced) == 0 and len(pieces) > 0,
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
            cuts = compute_cuts(layout, kerf=float(kerf))
            result["layouts"].append({
                "sheet_width": layout.stock.width,
                "sheet_height": layout.stock.height,
                "pieces_count": len(layout.placements),
                "waste": waste,
                "efficiency": (used_area / total_area * 100) if total_area > 0 else 0.0,
                "cuts": [
                    {
                        "number": cut.number,
                        "orientation": cut.orientation,
                        "position": cut.position,
                    }
                    for cut in cuts
                ],
                "placements": [
                    {
                        "x": p.x,
                        "y": p.y,
                        "placed_width": p.placed_width,
                        "placed_height": p.placed_height,
                        "label": p.piece.label or f"{p.piece.width:.0f}×{p.piece.height:.0f}",
                    }
                    for p in layout.placements
                ],
            })

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"success": False, "error": str(e),
                           "layouts_count": 0, "unplaced_count": 0, "layouts": []})
