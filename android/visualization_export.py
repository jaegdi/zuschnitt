"""
Minimal PDF export for the Android Kivy version.
Uses only reportlab (no PySide6 / Qt).
"""

from __future__ import annotations
from pathlib import Path

from core.models import Project, SheetLayout
from core.cuts import compute_cuts


def _hex_to_rgb_01(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def export_pdf_android(project: Project, out_path: Path) -> None:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    layouts = project.sheet_layouts if project.mode == "2d" else project.bar_layouts
    if not layouts:
        raise ValueError("No layouts to export. Run optimization first.")

    c = rl_canvas.Canvas(str(out_path))

    for idx, layout in enumerate(layouts):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(
            20 * mm,
            287 * mm,
            f"Sheet #{idx + 1}  {layout.stock.width:.0f}×{layout.stock.height:.0f} mm"
            f"  waste {layout.waste_pct():.1f}%",
        )

        sw, sh = layout.stock.width, layout.stock.height
        PAGE_W, PAGE_H = 210 * mm, 297 * mm  # A4
        MARGIN = 20 * mm
        scale = min(
            (PAGE_W - MARGIN * 2) / sw,
            (PAGE_H - MARGIN * 3) / sh,
        )
        ox = MARGIN
        oy = MARGIN

        def px(x):
            return ox + x * scale

        def py(y):
            return oy + (sh - y) * scale  # flip Y

        # Sheet rect
        c.setLineWidth(1.5)
        c.rect(px(0), py(sh), sw * scale, sh * scale)

        # Pieces
        for pl in layout.placements:
            r, g, b = _hex_to_rgb_01(pl.piece.color or "#4e79a7")
            c.setFillColorRGB(r, g, b, 0.5)
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.5)
            c.rect(
                px(pl.x),
                py(pl.y + pl.placed_height),
                pl.placed_width * scale,
                pl.placed_height * scale,
                fill=1,
            )
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", max(6, int(min(pl.placed_width, pl.placed_height) * scale / 6)))
            name = pl.piece.label or ""
            dim = f"{pl.placed_width:.0f}×{pl.placed_height:.0f}"
            text = (name + "\n" + dim) if name else dim
            cx = px(pl.x + pl.placed_width / 2)
            cy = py(pl.y + pl.placed_height / 2)
            c.drawCentredString(cx, cy, text.replace("\n", " "))

        # Cut lines
        cuts = compute_cuts(layout)
        c.setStrokeColorRGB(0.75, 0.22, 0.17)
        c.setLineWidth(0.8)
        for cut in cuts:
            c.setDash([4, 3])
            if cut.orientation == "H":
                y_p = py(cut.position)
                c.line(px(0), y_p, px(sw), y_p)
            else:
                x_p = px(cut.position)
                c.line(x_p, py(0), x_p, py(sh))
        c.setDash([])

        c.showPage()

    c.save()
