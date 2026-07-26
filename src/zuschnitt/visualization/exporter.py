"""PDF and SVG export for cutting plans."""

from __future__ import annotations

from pathlib import Path

from zuschnitt.core.models import Project, SheetLayout, BarLayout

# ---------------------------------------------------------------------------
# SVG export
# ---------------------------------------------------------------------------

def _sheet_to_svg(layout: SheetLayout, unit: str = "mm") -> str:
    sw, sh = layout.stock.width, layout.stock.height
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{sw}{unit}" height="{sh}{unit}" '
        f'viewBox="0 0 {sw} {sh}">',
        f'<rect width="{sw}" height="{sh}" fill="#f5f5f0" stroke="#333" stroke-width="2"/>',
    ]
    for pl in layout.placements:
        x, y = pl.x, pl.y
        pw, ph = pl.placed_width, pl.placed_height
        color = pl.piece.color or "#4e79a7"
        label = pl.piece.label or f"{pw:.0f}×{ph:.0f}"
        lines.append(
            f'<rect x="{x}" y="{y}" width="{pw}" height="{ph}" '
            f'fill="{color}" fill-opacity="0.8" stroke="black" stroke-width="1"/>'
        )
        fx = x + pw / 2
        fy = y + ph / 2
        fs = max(8, int(min(pw, ph) / 5))
        lines.append(
            f'<text x="{fx}" y="{fy}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="Arial" font-size="{fs}" fill="black">{label}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


def _bar_to_svg(layout: BarLayout, unit: str = "mm") -> str:
    blen = layout.stock.length
    h = 60
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{blen}{unit}" height="{h}{unit}" '
        f'viewBox="0 0 {blen} {h}">',
        f'<rect width="{blen}" height="{h}" fill="#f5f5f0" stroke="#333" stroke-width="2"/>',
    ]
    for pl in layout.placements:
        x = pl.offset
        w = pl.piece.length
        color = pl.piece.color or "#4e79a7"
        label = pl.piece.label or f"{w:.0f}"
        lines.append(
            f'<rect x="{x}" y="0" width="{w}" height="{h}" '
            f'fill="{color}" fill-opacity="0.8" stroke="black" stroke-width="1"/>'
        )
        fs = 10
        lines.append(
            f'<text x="{x + w/2}" y="{h/2}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="Arial" font-size="{fs}" fill="black">{label}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


def export_svg(project: Project, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    unit = project.settings.unit
    if project.mode == "2d":
        for i, layout in enumerate(project.sheet_layouts):
            svg = _sheet_to_svg(layout, unit)
            (folder / f"sheet_{i+1:02d}.svg").write_text(svg, encoding="utf-8")
    else:
        for i, layout in enumerate(project.bar_layouts):
            svg = _bar_to_svg(layout, unit)
            (folder / f"bar_{i+1:02d}.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# PDF export (via reportlab)
# ---------------------------------------------------------------------------

def export_pdf(project: Project, path: Path) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen.canvas import Canvas as RLCanvas
        from reportlab.lib import colors
    except ImportError as e:
        raise RuntimeError("reportlab is required for PDF export. Install it with: pip install reportlab") from e

    PAGE_W, PAGE_H = A4
    MARGIN = 20 * mm

    c = RLCanvas(str(path), pagesize=A4)

    def _draw_title(c, title: str, y: float) -> float:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(MARGIN, y, title)
        return y - 8 * mm

    def _draw_sheet_page(c, layout: SheetLayout, idx: int):
        c.setFont("Helvetica-Bold", 12)
        label = layout.stock.label or f"Sheet {idx}"
        c.drawString(MARGIN, PAGE_H - MARGIN, f"Layout: {label}")
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, PAGE_H - MARGIN - 6*mm,
                     f"Size: {layout.stock.width:.1f} × {layout.stock.height:.1f} mm  |  "
                     f"Waste: {layout.waste_pct():.1f}%  |  "
                     f"Pieces: {len(layout.placements)}")

        draw_y = PAGE_H - MARGIN - 15 * mm
        draw_h = draw_y - MARGIN
        draw_w = PAGE_W - 2 * MARGIN

        sw, sh = layout.stock.width, layout.stock.height
        scale = min(draw_w / sw, draw_h / sh)

        ox = MARGIN
        oy = MARGIN

        # Sheet outline
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.setFillColorRGB(0.96, 0.96, 0.94)
        c.rect(ox, oy, sw * scale, sh * scale, fill=1)

        # Pieces
        from reportlab.lib.colors import HexColor
        for pl in layout.placements:
            px = ox + pl.x * scale
            py = oy + (sh - pl.y - pl.placed_height) * scale
            pw = pl.placed_width * scale
            ph = pl.placed_height * scale
            hex_color = pl.piece.color or "#4e79a7"
            rgb = HexColor(hex_color)
            c.setFillColor(rgb)
            c.setStrokeColorRGB(0, 0, 0)
            c.rect(px, py, pw, ph, fill=1, stroke=1)
            lbl = pl.piece.label or f"{pl.placed_width:.0f}×{pl.placed_height:.0f}"
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", max(5, int(min(pw, ph) / 4)))
            c.drawCentredString(px + pw / 2, py + ph / 2, lbl)

        c.showPage()

    def _draw_bar_page(c, layout: BarLayout, idx: int):
        c.setFont("Helvetica-Bold", 12)
        label = layout.stock.label or f"Bar {idx}"
        c.drawString(MARGIN, PAGE_H - MARGIN, f"Layout: {label}")
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, PAGE_H - MARGIN - 6*mm,
                     f"Length: {layout.stock.length:.1f} mm  |  "
                     f"Waste: {layout.waste_pct():.1f}%  |  "
                     f"Pieces: {len(layout.placements)}")

        draw_w = PAGE_W - 2 * MARGIN
        bar_h = 30 * mm
        blen = layout.stock.length
        scale = draw_w / blen
        ox = MARGIN
        oy = PAGE_H / 2

        c.setFillColorRGB(0.96, 0.96, 0.94)
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.rect(ox, oy, draw_w, bar_h, fill=1)

        from reportlab.lib.colors import HexColor
        for pl in layout.placements:
            px = ox + pl.offset * scale
            pw = pl.piece.length * scale
            rgb = HexColor(pl.piece.color or "#4e79a7")
            c.setFillColor(rgb)
            c.rect(px, oy, pw, bar_h, fill=1, stroke=1)
            lbl = pl.piece.label or f"{pl.piece.length:.0f}"
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 8)
            c.drawCentredString(px + pw / 2, oy + bar_h / 2, lbl)

        c.showPage()

    if project.mode == "2d":
        for i, layout in enumerate(project.sheet_layouts):
            _draw_sheet_page(c, layout, i + 1)
    else:
        for i, layout in enumerate(project.bar_layouts):
            _draw_bar_page(c, layout, i + 1)

    c.save()
