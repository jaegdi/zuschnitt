"""
Minimal PDF export for the Android Kivy version.
Uses fpdf2 (pure Python, no native compilation needed for Android).
"""

from __future__ import annotations
from pathlib import Path

from core.models import Project
from core.cuts import compute_cuts


def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def export_pdf_android(project: Project, out_path: Path) -> None:
    from fpdf import FPDF

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    layouts = project.sheet_layouts if project.mode == "2d" else project.bar_layouts
    if not layouts:
        raise ValueError("No layouts to export. Run optimization first.")

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    PAGE_W, PAGE_H = 210, 297  # A4 mm

    for idx, layout in enumerate(layouts):
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_xy(10, 8)
        pdf.cell(
            0, 8,
            f"Sheet #{idx + 1}  {layout.stock.width:.0f}x{layout.stock.height:.0f} mm"
            f"  waste {layout.waste_pct():.1f}%",
        )

        sw, sh = layout.stock.width, layout.stock.height
        MARGIN = 15
        scale = min(
            (PAGE_W - MARGIN * 2) / sw,
            (PAGE_H - MARGIN * 3) / sh,
        )
        ox = MARGIN
        oy = MARGIN + 14  # below title

        def px(x): return ox + x * scale
        def py(y): return oy + y * scale

        # Sheet outline
        pdf.set_draw_color(50, 50, 50)
        pdf.set_line_width(0.5)
        pdf.rect(px(0), py(0), sw * scale, sh * scale)

        # Pieces
        for pl in layout.placements:
            r, g, b = _hex_to_rgb(pl.piece.color or "#4e79a7")
            pdf.set_fill_color(r, g, b)
            pdf.set_draw_color(0, 0, 0)
            pdf.set_line_width(0.3)
            pdf.rect(
                px(pl.x), py(pl.y),
                pl.placed_width * scale, pl.placed_height * scale,
                style="FD",
            )
            # Label
            fs = max(6, int(min(pl.placed_width, pl.placed_height) * scale / 7))
            pdf.set_font("Helvetica", "", fs)
            pdf.set_text_color(0, 0, 0)
            name = pl.piece.label or ""
            dim = f"{pl.placed_width:.0f}x{pl.placed_height:.0f}"
            text = f"{name} {dim}".strip()
            cx = px(pl.x + pl.placed_width / 2)
            cy = py(pl.y + pl.placed_height / 2)
            tw = pdf.get_string_width(text)
            pdf.set_xy(cx - tw / 2, cy - fs / 2)
            pdf.cell(tw, fs, text)

        # Cut lines (dashed red)
        cuts = compute_cuts(layout)
        pdf.set_draw_color(190, 56, 44)
        pdf.set_line_width(0.4)
        pdf.set_dash_pattern(dash=2, gap=1.5)
        for cut in cuts:
            if cut.orientation == "H":
                y_p = py(cut.position)
                pdf.line(px(0), y_p, px(sw), y_p)
                # Number label
                pdf.set_font("Helvetica", "B", 6)
                pdf.set_xy(px(sw) + 1, y_p - 2)
                pdf.cell(5, 4, str(cut.number))
            else:
                x_p = px(cut.position)
                pdf.line(x_p, py(0), x_p, py(sh))
                pdf.set_font("Helvetica", "B", 6)
                pdf.set_xy(x_p - 2, py(0) - 4)
                pdf.cell(5, 4, str(cut.number))
        pdf.set_dash_pattern()  # reset

    pdf.output(str(out_path))
