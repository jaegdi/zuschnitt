"""PDF and SVG export for cutting plans."""

from __future__ import annotations

from pathlib import Path

from zuschnitt.core.models import Project, SheetLayout, BarLayout
from zuschnitt.core.cuts import compute_cuts, CutLine
from zuschnitt.visualization.cut_label_layout import (
    place_horizontal_cut_markers,
    place_vertical_cut_markers,
)

# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

_DIM = 50   # extra viewBox margin for dimension annotations outside the sheet


def _svg_line(x1, y1, x2, y2, stroke, stroke_w=1, dash="") -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{stroke_w}"{dash_attr}/>')


def _svg_text(x, y, text, font_size=10, anchor="middle", fill="black",
              bold=False, transform="") -> str:
    weight = ' font-weight="bold"' if bold else ""
    t = f' transform="{transform}"' if transform else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" font-family="Arial" '
            f'font-size="{font_size}"{weight} fill="{fill}"{t}>{text}</text>')


def _svg_circle(cx, cy, r, fill, stroke="white") -> str:
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'


def _svg_arrow(x1, y1, x2, y2, stroke="#444", w=1) -> list[str]:
    import math
    lines = [_svg_line(x1, y1, x2, y2, stroke, w)]
    for ax, ay, bx, by in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
        angle = math.atan2(by - ay, bx - ax)
        for side in (+1, -1):
            lx = ax + 8 * math.cos(angle + side * math.radians(150))
            ly = ay + 8 * math.sin(angle + side * math.radians(150))
            lines.append(_svg_line(ax, ay, lx, ly, stroke, w))
    return lines


# ---------------------------------------------------------------------------
# SVG: sheet layout
# ---------------------------------------------------------------------------

def _sheet_to_svg(layout: SheetLayout, unit: str = "mm", kerf: float = 0.0) -> str:
    sw, sh = layout.stock.width, layout.stock.height
    D = _DIM
    VW = sw + 2 * D
    VH = sh + 2 * D
    OX, OY = D, D   # offset of sheet top-left inside the viewBox

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{VW}{unit}" height="{VH}{unit}" '
        f'viewBox="0 0 {VW} {VH}">',
        # Sheet background
        f'<rect x="{OX}" y="{OY}" width="{sw}" height="{sh}" '
        f'fill="#f5f5f0" stroke="#333" stroke-width="2"/>',
    ]

    fs = max(8, int(min(sw, sh) / 50))

    # Overall width dimension (above)
    ay = OY - 18
    parts += _svg_arrow(OX, ay, OX + sw, ay)
    parts.append(_svg_line(OX, OY, OX, ay - 3, "#444"))
    parts.append(_svg_line(OX + sw, OY, OX + sw, ay - 3, "#444"))
    parts.append(_svg_text(OX + sw / 2, ay, f"{sw:.0f}", font_size=fs - 1, fill="#222"))

    # Overall height dimension (left)
    ax = OX - 18
    parts += _svg_arrow(ax, OY, ax, OY + sh)
    parts.append(_svg_line(OX, OY, ax - 3, OY, "#444"))
    parts.append(_svg_line(OX, OY + sh, ax - 3, OY + sh, "#444"))
    parts.append(_svg_text(ax, OY + sh / 2, f"{sh:.0f}", font_size=fs - 1, fill="#222",
                           transform=f"rotate(-90,{ax},{OY + sh / 2})"))

    # Reference dot (green at origin)
    parts.append(_svg_circle(OX, OY, 5, "#27ae60"))

    # Pieces
    for pl in layout.placements:
        x, y = pl.x + OX, pl.y + OY
        pw, ph = pl.placed_width, pl.placed_height
        color = pl.piece.color or "#4e79a7"
        name = pl.piece.label or ""
        rot = " ↻" if pl.rotated else ""
        dim_str = f"{pw:.0f} × {ph:.0f}"

        parts.append(f'<rect x="{x}" y="{y}" width="{pw}" height="{ph}" '
                     f'fill="{color}" fill-opacity="0.8" stroke="black" stroke-width="1"/>')
        if name:
            parts.append(_svg_text(x + pw / 2, y + ph / 2 - fs, name + rot, font_size=fs, bold=True))
            parts.append(_svg_text(x + pw / 2, y + ph / 2 + fs, dim_str, font_size=fs))
        else:
            parts.append(_svg_text(x + pw / 2, y + ph / 2, dim_str + rot, font_size=fs))

    # Cut lines, dimension ticks, numbered circles
    cuts = compute_cuts(layout, kerf=kerf)
    cut_values = {cut.number: cut.position for cut in cuts}
    CIRCLE_R = max(7, int(min(sw, sh) / 55))
    h_svg_cuts = [
        CutLine(number=cut.number, orientation=cut.orientation, position=OY + cut.position)
        for cut in cuts if cut.orientation == "H"
    ]
    v_svg_cuts = [
        CutLine(number=cut.number, orientation=cut.orientation, position=OX + cut.position)
        for cut in cuts if cut.orientation == "V"
    ]
    h_markers = place_horizontal_cut_markers(
        h_svg_cuts,
        anchor_x=OX + sw,
        label_x=OX + sw + CIRCLE_R + 18,
        min_sep=CIRCLE_R * 2 + 6,
    )
    v_markers = place_vertical_cut_markers(
        v_svg_cuts,
        anchor_y=OY + sh,
        label_y=OY + sh + CIRCLE_R + 26,
        min_sep=CIRCLE_R * 2 + 6,
    )
    h_dim_markers = place_horizontal_cut_markers(
        h_svg_cuts,
        anchor_x=OX,
        label_x=OX - 18,
        min_sep=18,
    )
    v_dim_markers = place_vertical_cut_markers(
        v_svg_cuts,
        anchor_y=OY,
        label_y=OY - 18,
        min_sep=18,
    )

    for cut in cuts:
        if cut.orientation == "H":
            cy = OY + cut.position
            parts.append(_svg_line(OX, cy, OX + sw, cy, "#c0392b", 1.5, "6,4"))
            # Tick + label on left
            parts.append(_svg_line(OX - 16, cy, OX, cy, "#444"))
        else:
            cx2 = OX + cut.position
            parts.append(_svg_line(cx2, OY, cx2, OY + sh, "#c0392b", 1.5, "6,4"))
            # Tick + label on top
            parts.append(_svg_line(cx2, OY - 16, cx2, OY, "#444"))

    for marker in h_dim_markers:
        parts.append(_svg_line(
            marker.anchor_x - 16,
            marker.anchor_y,
            marker.label_x + 4,
            marker.label_y,
            "#444",
            1,
        ))
        parts.append(_svg_text(marker.label_x, marker.label_y, f"{cut_values[marker.cut.number]:.0f}",
                               font_size=fs - 2, anchor="end", fill="#555"))

    for marker in v_dim_markers:
        parts.append(_svg_line(
            marker.anchor_x,
            marker.anchor_y - 16,
            marker.label_x,
            marker.label_y + 4,
            "#444",
            1,
        ))
        parts.append(_svg_text(marker.label_x, marker.label_y, f"{cut_values[marker.cut.number]:.0f}",
                               font_size=fs - 2, fill="#555"))

    for marker in h_markers:
        parts.append(_svg_line(
            marker.anchor_x,
            marker.anchor_y,
            marker.label_x - CIRCLE_R - 2,
            marker.label_y,
            "#c0392b",
            1,
        ))
        parts.append(_svg_circle(marker.label_x, marker.label_y, CIRCLE_R, "#c0392b"))
        parts.append(_svg_text(marker.label_x, marker.label_y, str(marker.cut.number),
                               font_size=max(6, CIRCLE_R - 2), fill="white"))

    for marker in v_markers:
        parts.append(_svg_line(
            marker.anchor_x,
            marker.anchor_y,
            marker.label_x,
            marker.label_y - CIRCLE_R - 2,
            "#c0392b",
            1,
        ))
        parts.append(_svg_circle(marker.label_x, marker.label_y, CIRCLE_R, "#c0392b"))
        parts.append(_svg_text(marker.label_x, marker.label_y, str(marker.cut.number),
                               font_size=max(6, CIRCLE_R - 2), fill="white"))

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SVG: bar layout
# ---------------------------------------------------------------------------

def _bar_to_svg(layout: BarLayout, unit: str = "mm") -> str:
    blen = layout.stock.length
    H = 60
    D = _DIM
    VW = blen + 2 * D
    VH = H + 2 * D
    OX, OY = D, D

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{VW}{unit}" height="{VH}{unit}" '
        f'viewBox="0 0 {VW} {VH}">',
        f'<rect x="{OX}" y="{OY}" width="{blen}" height="{H}" '
        f'fill="#f5f5f0" stroke="#333" stroke-width="2"/>',
    ]

    # Overall length dimension
    ay = OY - 18
    parts += _svg_arrow(OX, ay, OX + blen, ay)
    parts.append(_svg_line(OX, OY, OX, ay - 3, "#444"))
    parts.append(_svg_line(OX + blen, OY, OX + blen, ay - 3, "#444"))
    parts.append(_svg_text(OX + blen / 2, ay, f"{blen:.0f}", font_size=9, fill="#222"))

    # Reference dot
    parts.append(_svg_circle(OX, OY + H / 2, 5, "#27ae60"))

    CIRCLE_R = 8
    cut_num = 0
    for pl in layout.placements:
        x = OX + pl.offset
        w = pl.piece.length
        color = pl.piece.color or "#4e79a7"
        label = pl.piece.label or ""

        parts.append(f'<rect x="{x}" y="{OY}" width="{w}" height="{H}" '
                     f'fill="{color}" fill-opacity="0.8" stroke="black" stroke-width="1"/>')
        cy = OY + H / 2
        if label:
            parts.append(_svg_text(x + w / 2, cy - 8, label, font_size=9, bold=True))
        parts.append(_svg_text(x + w / 2, cy + 6, f"{w:.0f}", font_size=9))

        # Cut line at right edge
        cut_x = pl.offset + w
        if cut_x < blen - 0.5:
            cut_num += 1
            svgx = OX + cut_x
            parts.append(_svg_line(svgx, OY, svgx, OY + H, "#c0392b", 1.5, "6,4"))
            parts.append(_svg_line(svgx, OY + H, svgx, OY + H + 15, "#444"))
            parts.append(_svg_text(svgx, OY + H + 22, f"{cut_x:.0f}", font_size=8, fill="#555"))
            parts.append(_svg_circle(svgx, OY + H + 22 + CIRCLE_R + 6, CIRCLE_R, "#c0392b"))
            parts.append(_svg_text(svgx, OY + H + 22 + CIRCLE_R + 6, str(cut_num),
                                   font_size=7, fill="white"))

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public export functions
# ---------------------------------------------------------------------------

def export_svg(project: Project, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    unit = project.settings.unit
    base = project.name or "cutting_plan"
    # Strip characters unsafe for filenames
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in base).strip()
    if project.mode == "2d":
        for i, layout in enumerate(project.sheet_layouts):
            svg = _sheet_to_svg(layout, unit, kerf=project.settings.kerf)
            (folder / f"{safe}_sheet_{i+1:02d}.svg").write_text(svg, encoding="utf-8")
    else:
        for i, layout in enumerate(project.bar_layouts):
            svg = _bar_to_svg(layout, unit)
            (folder / f"{safe}_bar_{i+1:02d}.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# PDF export (via reportlab)
# ---------------------------------------------------------------------------

def export_pdf(project: Project, path: Path) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen.canvas import Canvas as RLCanvas
        from reportlab.lib.colors import HexColor, Color
    except ImportError as e:
        raise RuntimeError(
            "reportlab is required for PDF export. Install with: pip install reportlab"
        ) from e

    PAGE_W, PAGE_H = A4
    MARGIN = 15 * mm
    DIM_SPACE = 12 * mm   # space reserved for dim lines outside the drawn sheet

    rl = RLCanvas(str(path), pagesize=A4)

    def _rl_arrow(c, x1, y1, x2, y2, size=5):
        import math
        c.line(x1, y1, x2, y2)
        for ax, ay, bx, by in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
            angle = math.atan2(by - ay, bx - ax)
            for side in (+1, -1):
                lx = ax + size * math.cos(angle + side * math.radians(150))
                ly = ay + size * math.sin(angle + side * math.radians(150))
                c.line(ax, ay, lx, ly)

    def _draw_sheet_page(c, layout: SheetLayout, idx: int):
        sw, sh = layout.stock.width, layout.stock.height
        title = layout.stock.label or f"Sheet {idx}"

        c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN, PAGE_H - MARGIN, f"Layout: {title}")
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN, PAGE_H - MARGIN - 5 * mm,
                     f"Size: {sw:.1f} × {sh:.1f} mm  |  "
                     f"Waste: {layout.waste_pct():.1f}%  |  "
                     f"Pieces: {len(layout.placements)}")

        # Available draw area (leave room for dim annotations around the sheet)
        area_x0 = MARGIN + DIM_SPACE
        area_y0 = MARGIN + DIM_SPACE
        area_w = PAGE_W - 2 * MARGIN - 2 * DIM_SPACE
        area_h = PAGE_H - 2 * MARGIN - 2 * DIM_SPACE - 10 * mm

        scale = min(area_w / sw, area_h / sh)
        # Centre the sheet in the available area
        ox = area_x0 + (area_w - sw * scale) / 2
        oy = area_y0 + (area_h - sh * scale) / 2

        def sy(y_mm):
            """Convert mm from top to PDF y (bottom-up), scaling."""
            return oy + (sh - y_mm) * scale

        # Sheet outline
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.setFillColorRGB(0.96, 0.96, 0.94)
        c.rect(ox, oy, sw * scale, sh * scale, fill=1, stroke=1)

        # Pieces
        for pl in layout.placements:
            px = ox + pl.x * scale
            py_top = sy(pl.y)
            pw = pl.placed_width * scale
            ph = pl.placed_height * scale
            py = py_top - ph
            rgb = HexColor(pl.piece.color or "#4e79a7")
            c.setFillColor(rgb)
            c.setStrokeColorRGB(0, 0, 0)
            c.rect(px, py, pw, ph, fill=1, stroke=1)
            name = pl.piece.label or ""
            dim_str = f"{pl.placed_width:.0f}×{pl.placed_height:.0f}"
            rot = "↻" if pl.rotated else ""
            c.setFillColorRGB(0, 0, 0)
            fs = max(5, int(min(pw, ph) / 5))
            c.setFont("Helvetica-Bold" if name else "Helvetica", fs)
            cx = px + pw / 2
            if name:
                c.drawCentredString(cx, py + ph / 2 + fs * 0.3, name + rot)
                c.setFont("Helvetica", fs)
                c.drawCentredString(cx, py + ph / 2 - fs * 0.8, dim_str)
            else:
                c.drawCentredString(cx, py + ph / 2, dim_str + rot)

        # Overall dimension lines
        c.setStrokeColorRGB(0.27, 0.27, 0.27)
        c.setFillColorRGB(0.13, 0.13, 0.13)
        c.setLineWidth(0.5)
        c.setFont("Helvetica", 7)

        # Width arrow above sheet
        aw_y = oy + sh * scale + 8 * mm
        _rl_arrow(c, ox, aw_y, ox + sw * scale, aw_y)
        c.line(ox, oy + sh * scale, ox, aw_y + 2)
        c.line(ox + sw * scale, oy + sh * scale, ox + sw * scale, aw_y + 2)
        c.drawCentredString(ox + sw * scale / 2, aw_y + 1.5 * mm, f"{sw:.0f} mm")

        # Height arrow to left of sheet
        ah_x = ox - 8 * mm
        _rl_arrow(c, ah_x, oy, ah_x, oy + sh * scale)
        c.line(ox, oy, ah_x - 2, oy)
        c.line(ox, oy + sh * scale, ah_x - 2, oy + sh * scale)
        c.saveState()
        c.translate(ah_x - 1.5 * mm, oy + sh * scale / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, f"{sh:.0f} mm")
        c.restoreState()

        # Reference dot
        c.setFillColorRGB(0.15, 0.68, 0.38)
        c.circle(ox, oy + sh * scale, 3 * mm, fill=1, stroke=0)

        # Cut lines
        cuts = compute_cuts(layout, kerf=project.settings.kerf)
        cut_values = {cut.number: cut.position for cut in cuts}
        H_CIRCLE_R = 2.8 * mm
        V_CIRCLE_R = 2.4 * mm
        h_pdf_cuts = [
            CutLine(number=cut.number, orientation=cut.orientation, position=sy(cut.position))
            for cut in cuts if cut.orientation == "H"
        ]
        v_pdf_cuts = [
            CutLine(number=cut.number, orientation=cut.orientation, position=ox + cut.position * scale)
            for cut in cuts if cut.orientation == "V"
        ]
        h_markers = place_horizontal_cut_markers(
            h_pdf_cuts,
            anchor_x=ox + sw * scale,
            label_x=ox + sw * scale + H_CIRCLE_R + 2.5 * mm,
            min_sep=H_CIRCLE_R * 2 + 1.2 * mm,
        )
        v_markers = place_vertical_cut_markers(
            v_pdf_cuts,
            anchor_y=oy,
            label_y=oy - V_CIRCLE_R - 10 * mm,
            min_sep=V_CIRCLE_R * 2 + 3.5 * mm,
        )
        h_dim_markers = place_horizontal_cut_markers(
            h_pdf_cuts,
            anchor_x=ox,
            label_x=ox - 6.5 * mm,
            min_sep=5 * mm,
        )
        v_dim_markers = place_vertical_cut_markers(
            v_pdf_cuts,
            anchor_y=oy + sh * scale,
            label_y=oy + sh * scale + 7 * mm,
            min_sep=7 * mm,
        )

        for cut in cuts:
            c.setStrokeColor(HexColor("#c0392b"))
            c.setDash(4, 3)
            c.setLineWidth(0.8)

            if cut.orientation == "H":
                pdf_y = sy(cut.position)
                c.line(ox, pdf_y, ox + sw * scale, pdf_y)
                c.setStrokeColorRGB(0.27, 0.27, 0.27)
                c.setLineWidth(0.5)
                c.line(ox - 5 * mm, pdf_y, ox, pdf_y)
            else:
                pdf_x = ox + cut.position * scale
                pdf_y0 = oy
                pdf_y1 = oy + sh * scale
                c.line(pdf_x, pdf_y0, pdf_x, pdf_y1)
                c.setStrokeColorRGB(0.27, 0.27, 0.27)
                c.setLineWidth(0.5)
                c.line(pdf_x, pdf_y1, pdf_x, pdf_y1 + 5 * mm)
            c.setDash()

        c.setStrokeColorRGB(0.33, 0.33, 0.33)
        c.setFillColorRGB(0.33, 0.33, 0.33)
        c.setLineWidth(0.5)
        c.setFont("Helvetica", 6)
        for marker in h_dim_markers:
            c.line(
                marker.anchor_x - 5 * mm,
                marker.anchor_y,
                marker.label_x + 1.2 * mm,
                marker.label_y,
            )
            c.drawRightString(marker.label_x, marker.label_y - 2, f"{cut_values[marker.cut.number]:.0f}")

        for marker in v_dim_markers:
            c.line(
                marker.anchor_x,
                marker.anchor_y + 5 * mm,
                marker.label_x,
                marker.label_y - 1.5 * mm,
            )
            c.drawCentredString(marker.label_x, marker.label_y - 1.5, f"{cut_values[marker.cut.number]:.0f}")

        c.setStrokeColor(HexColor("#c0392b"))
        c.setLineWidth(0.6)
        for marker in h_markers:
            c.line(
                marker.anchor_x,
                marker.anchor_y,
                marker.label_x - H_CIRCLE_R - 1.2,
                marker.label_y,
            )
            c.setFillColor(HexColor("#c0392b"))
            c.circle(marker.label_x, marker.label_y, H_CIRCLE_R, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(marker.label_x, marker.label_y - 1.2, str(marker.cut.number))

        for marker in v_markers:
            c.line(
                marker.anchor_x,
                marker.anchor_y,
                marker.label_x,
                marker.label_y + V_CIRCLE_R + 1.2,
            )
            c.setFillColor(HexColor("#c0392b"))
            c.circle(marker.label_x, marker.label_y, V_CIRCLE_R, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 4)
            c.drawCentredString(marker.label_x, marker.label_y - 1.1, str(marker.cut.number))

        c.setDash()
        c.showPage()

    def _draw_bar_page(c, layout: BarLayout, idx: int):
        blen = layout.stock.length
        title = layout.stock.label or f"Bar {idx}"

        c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN, PAGE_H - MARGIN, f"Layout: {title}")
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN, PAGE_H - MARGIN - 5 * mm,
                     f"Length: {blen:.1f} mm  |  "
                     f"Waste: {layout.waste_pct():.1f}%  |  "
                     f"Pieces: {len(layout.placements)}")

        draw_w = PAGE_W - 2 * MARGIN - 2 * DIM_SPACE
        bar_h = 20 * mm
        scale = draw_w / blen
        ox = MARGIN + DIM_SPACE
        oy = PAGE_H / 2

        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.setFillColorRGB(0.96, 0.96, 0.94)
        c.rect(ox, oy, draw_w, bar_h, fill=1)

        # Overall length dimension
        c.setFont("Helvetica", 7)
        c.setLineWidth(0.5)
        aw_y = oy + bar_h + 6 * mm
        _rl_arrow(c, ox, aw_y, ox + draw_w, aw_y)
        c.line(ox, oy + bar_h, ox, aw_y + 2)
        c.line(ox + draw_w, oy + bar_h, ox + draw_w, aw_y + 2)
        c.drawCentredString(ox + draw_w / 2, aw_y + 1.5 * mm, f"{blen:.0f} mm")

        # Reference dot
        c.setFillColorRGB(0.15, 0.68, 0.38)
        c.circle(ox, oy + bar_h / 2, 2 * mm, fill=1, stroke=0)

        CIRCLE_R = 3 * mm
        cut_num = 0
        for pl in layout.placements:
            px = ox + pl.offset * scale
            pw = pl.piece.length * scale
            rgb = HexColor(pl.piece.color or "#4e79a7")
            c.setFillColor(rgb)
            c.setStrokeColorRGB(0, 0, 0)
            c.rect(px, oy, pw, bar_h, fill=1, stroke=1)

            name = pl.piece.label or ""
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold" if name else "Helvetica", 7)
            if name:
                c.drawCentredString(px + pw / 2, oy + bar_h / 2 + 2 * mm, name)
                c.setFont("Helvetica", 6)
                c.drawCentredString(px + pw / 2, oy + bar_h / 2 - 2 * mm,
                                    f"{pl.piece.length:.0f}")
            else:
                c.drawCentredString(px + pw / 2, oy + bar_h / 2, f"{pl.piece.length:.0f}")

            cut_x = pl.offset + pl.piece.length
            if cut_x < blen - 0.5:
                cut_num += 1
                sx = ox + cut_x * scale
                c.setStrokeColor(HexColor("#c0392b"))
                c.setDash(4, 3)
                c.setLineWidth(0.8)
                c.line(sx, oy, sx, oy + bar_h)
                c.setDash()
                c.setStrokeColorRGB(0.27, 0.27, 0.27)
                c.setLineWidth(0.5)
                c.line(sx, oy, sx, oy - 5 * mm)
                c.setFillColorRGB(0.33, 0.33, 0.33)
                c.setFont("Helvetica", 6)
                c.drawCentredString(sx, oy - 6.5 * mm, f"{cut_x:.0f}")
                c.setFillColor(HexColor("#c0392b"))
                c.circle(sx, oy - 6.5 * mm - CIRCLE_R - 1 * mm, CIRCLE_R, fill=1, stroke=0)
                c.setFillColorRGB(1, 1, 1)
                c.setFont("Helvetica-Bold", 5)
                c.drawCentredString(sx, oy - 6.5 * mm - CIRCLE_R - 1 * mm - 1.5, str(cut_num))

        c.setDash()
        c.showPage()

    if project.mode == "2d":
        for i, layout in enumerate(project.sheet_layouts):
            _draw_sheet_page(rl, layout, i + 1)
    else:
        for i, layout in enumerate(project.bar_layouts):
            _draw_bar_page(rl, layout, i + 1)

    rl.save()
