"""
Simple bridge for calling the Zuschnitt optimizer from Kotlin/Android.

This module provides a simplified API that Kotlin can call via Chaquopy.
"""

from zuschnitt.models import (
    Project, Settings, StockSheet, Piece, Dimension, LayoutAssignment
)
from zuschnitt.optimizer_2d import optimize_2d


def optimize_simple(sheets_data, pieces_data, kerf=3.0):
    """
    Simplified optimizer entry point for Android.
    
    Args:
        sheets_data: List of dicts with 'width', 'height', 'quantity' keys
        pieces_data: List of dicts with 'width', 'height', 'quantity' keys
        kerf: Cut width in mm (default: 3.0)
    
    Returns:
        Dict with 'success', 'layouts', 'waste' keys
    """
    try:
        # Convert input data to model objects
        sheets = []
        for i, sheet_dict in enumerate(sheets_data):
            sheet = StockSheet(
                id=f"sheet_{i}",
                dimension=Dimension(
                    width=float(sheet_dict["width"]),
                    height=float(sheet_dict["height"])
                ),
                quantity=int(sheet_dict.get("quantity", 1))
            )
            sheets.append(sheet)
        
        pieces = []
        for i, piece_dict in enumerate(pieces_data):
            piece = Piece(
                id=f"piece_{i}",
                dimension=Dimension(
                    width=float(piece_dict["width"]),
                    height=float(piece_dict["height"])
                ),
                quantity=int(piece_dict.get("quantity", 1)),
                can_rotate=piece_dict.get("can_rotate", True)
            )
            pieces.append(piece)
        
        # Create settings
        settings = Settings(
            kerf=kerf,
            trim_edges=False
        )
        
        # Run optimizer
        layouts, unplaced = optimize_2d(sheets, pieces, settings)
        
        # Convert results to JSON-serializable format
        result = {
            "success": len(unplaced) == 0,
            "layouts_count": len(layouts),
            "unplaced_count": len(unplaced),
            "total_waste": 0.0,
            "layouts": []
        }
        
        for layout in layouts:
            layout_dict = {
                "sheet_id": layout.sheet.id,
                "sheet_width": layout.sheet.dimension.width,
                "sheet_height": layout.sheet.dimension.height,
                "pieces_count": len(layout.assignments),
                "assignments": []
            }
            
            for assignment in layout.assignments:
                assignment_dict = {
                    "piece_id": assignment.piece.id,
                    "x": assignment.x,
                    "y": assignment.y,
                    "width": assignment.width,
                    "height": assignment.height,
                    "rotated": assignment.rotated
                }
                layout_dict["assignments"].append(assignment_dict)
            
            # Calculate waste
            used_area = sum(a.width * a.height for a in layout.assignments)
            total_area = layout.sheet.dimension.width * layout.sheet.dimension.height
            waste = total_area - used_area
            layout_dict["waste"] = waste
            layout_dict["efficiency"] = (used_area / total_area * 100) if total_area > 0 else 0
            
            result["total_waste"] += waste
            result["layouts"].append(layout_dict)
        
        if unplaced:
            result["unplaced"] = [
                {
                    "piece_id": p.id,
                    "width": p.dimension.width,
                    "height": p.dimension.height
                }
                for p in unplaced
            ]
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
