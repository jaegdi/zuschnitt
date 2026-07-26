"""
Kivy drawing widget for a 2D sheet layout.
Draws pieces, cut lines, numbered circles and dimension annotations.
"""

from __future__ import annotations
import math

from kivy.uix.widget import Widget
from kivy.graphics import (
    Color, Rectangle, Line, Ellipse, PushMatrix, PopMatrix, Rotate, Translate,
)
from kivy.graphics.context_instructions import Color as CColor
from kivy.core.text import Label as CoreLabel
from kivy.graphics.texture import Texture

from core.models import SheetLayout, BarLayout
from core.cuts import compute_cuts


def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


class SheetWidget(Widget):
    """Renders a 2-D sheet layout with pieces, cut lines and dimensions."""

    def __init__(self, layout: SheetLayout, **kwargs):
        super().__init__(**kwargs)
        self._layout = layout
        self.bind(size=self._redraw, pos=self._redraw)

    def _redraw(self, *_):
        self.canvas.clear()
        if not self._layout:
            return
        self._draw()

    def on_size(self, *_):
        self._redraw()

    def _draw(self):
        layout = self._layout
        sw, sh = layout.stock.width, layout.stock.height
        widget_w, widget_h = self.width, self.height

        MARGIN = 40
        scale = min((widget_w - MARGIN * 2) / sw, (widget_h - MARGIN * 2) / sh)
        ox = self.x + (widget_w - sw * scale) / 2
        oy = self.y + (widget_h - sh * scale) / 2

        def sx(x): return ox + x * scale
        def sy(y): return oy + (sh - y) * scale  # flip Y (Kivy bottom-up)

        with self.canvas:
            # Sheet background
            Color(0.96, 0.96, 0.94, 1)
            Rectangle(pos=(sx(0), sy(sh)), size=(sw * scale, sh * scale))
            Color(0.2, 0.2, 0.2, 1)
            Line(rectangle=(sx(0), sy(sh), sw * scale, sh * scale), width=1.5)

            # Pieces
            for pl in layout.placements:
                r, g, b = _hex_to_rgb(pl.piece.color or "#4e79a7")
                Color(r, g, b, 0.8)
                Rectangle(
                    pos=(sx(pl.x), sy(pl.y + pl.placed_height)),
                    size=(pl.placed_width * scale, pl.placed_height * scale),
                )
                Color(0, 0, 0, 1)
                Line(
                    rectangle=(
                        sx(pl.x), sy(pl.y + pl.placed_height),
                        pl.placed_width * scale, pl.placed_height * scale,
                    ),
                    width=0.8,
                )

            # Cut lines (dashed red)
            cuts = compute_cuts(layout)
            Color(0.75, 0.22, 0.17, 1)
            for cut in cuts:
                if cut.orientation == "H":
                    y_pdf = sy(cut.position)
                    Line(points=[sx(0), y_pdf, sx(sw), y_pdf],
                         width=1.0, dash_length=6, dash_offset=4)
                else:
                    x_pdf = sx(cut.position)
                    Line(points=[x_pdf, sy(0), x_pdf, sy(sh)],
                         width=1.0, dash_length=6, dash_offset=4)

        # Draw text labels using CoreLabel (Kivy texture approach)
        self._draw_labels(layout, sx, sy, sw, sh, scale)

    def _draw_labels(self, layout, sx, sy, sw, sh, scale):
        """Draw piece text and cut numbers as canvas textures."""
        cuts = compute_cuts(layout)
        CIRCLE_R = max(10, int(min(sw, sh) * scale / 50))

        with self.canvas:
            for pl in layout.placements:
                pw, ph = pl.placed_width * scale, pl.placed_height * scale
                cx = sx(pl.x + pl.placed_width / 2)
                cy = sy(pl.y + pl.placed_height / 2)
                name = pl.piece.label or ""
                dim = f"{pl.placed_width:.0f}×{pl.placed_height:.0f}"
                text = (name + "\n" + dim) if name else dim
                fs = max(10, int(min(pw, ph) / 6))
                self._draw_text(text, cx, cy, fs, (0, 0, 0, 1))

            # Cut line numbers
            for cut in cuts:
                if cut.orientation == "H":
                    cx = sx(sw) + CIRCLE_R + 4
                    cy = sy(cut.position)
                else:
                    cx = sx(cut.position)
                    cy = sy(sh) - CIRCLE_R - 4
                Color(0.75, 0.22, 0.17, 1)
                Ellipse(pos=(cx - CIRCLE_R, cy - CIRCLE_R),
                        size=(CIRCLE_R * 2, CIRCLE_R * 2))
                self._draw_text(str(cut.number), cx, cy,
                                max(8, CIRCLE_R - 2), (1, 1, 1, 1))

    def _draw_text(self, text: str, cx: float, cy: float,
                   font_size: int, color):
        lbl = CoreLabel(text=text, font_size=font_size, halign="center")
        lbl.refresh()
        texture = lbl.texture
        w, h = texture.size
        Color(*color)
        Rectangle(texture=texture,
                  pos=(cx - w / 2, cy - h / 2),
                  size=(w, h))
