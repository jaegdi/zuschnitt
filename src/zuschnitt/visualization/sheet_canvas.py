"""QGraphicsView-based canvas for displaying one sheet layout."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsPolygonItem,
)

from zuschnitt.core.models import SheetLayout, BarLayout

# ── helpers ──────────────────────────────────────────────────────────────────

def _add_text(scene, text: str, cx: float, cy: float, font: QFont,
              color=Qt.GlobalColor.black) -> QGraphicsTextItem:
    """Add centred text at (cx, cy) in scene coordinates."""
    item = QGraphicsTextItem(text)
    item.setFont(font)
    item.setDefaultTextColor(color)
    r = item.boundingRect()
    item.setPos(cx - r.width() / 2, cy - r.height() / 2)
    scene.addItem(item)
    return item


def _arrow_line(scene, x1: float, y1: float, x2: float, y2: float,
                pen: QPen, arrow_size: float = 8.0):
    """Draw a line with arrowheads at both ends."""
    scene.addItem(_make_line(x1, y1, x2, y2, pen))
    for (ax, ay, bx, by) in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
        angle = math.atan2(by - ay, bx - ax)
        for side in (+1, -1):
            lx = ax + arrow_size * math.cos(angle + side * math.radians(150))
            ly = ay + arrow_size * math.sin(angle + side * math.radians(150))
            scene.addItem(_make_line(ax, ay, lx, ly, pen))


def _make_line(x1, y1, x2, y2, pen: QPen) -> QGraphicsLineItem:
    item = QGraphicsLineItem(x1, y1, x2, y2)
    item.setPen(pen)
    return item


def _dim_pen() -> QPen:
    pen = QPen(QColor("#444444"), 1, Qt.PenStyle.SolidLine)
    return pen


# ── 2-D canvas ───────────────────────────────────────────────────────────────

class SheetCanvas(QGraphicsView):
    """Displays a 2-D sheet layout with color-coded piece rectangles and dimensions."""

    DIM_OFFSET = 25   # space outside the sheet reserved for dimension lines
    MARGIN = 10       # extra space around the whole drawing

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._layout: SheetLayout | None = None

    def set_layout(self, layout: SheetLayout) -> None:
        self._layout = layout
        self._draw()

    def _draw(self) -> None:
        self._scene.clear()
        if self._layout is None:
            return

        sheet = self._layout.stock
        sw, sh = sheet.width, sheet.height
        D = self.DIM_OFFSET

        piece_font_size = max(6, int(min(sw, sh) / 50))
        piece_font = QFont("Arial", piece_font_size)
        dim_font = QFont("Arial", max(5, piece_font_size - 1))
        dim_pen = _dim_pen()

        # ── Sheet background ──────────────────────────────────────────────
        bg = QGraphicsRectItem(QRectF(0, 0, sw, sh))
        bg.setBrush(QBrush(QColor("#f5f5f0")))
        bg.setPen(QPen(QColor("#333333"), 2))
        self._scene.addItem(bg)

        # ── Sheet overall dimensions ──────────────────────────────────────
        # Width arrow above the sheet
        _arrow_line(self._scene, 0, -D, sw, -D, dim_pen)
        # extension lines
        self._scene.addItem(_make_line(0, 0, 0, -D - 4, dim_pen))
        self._scene.addItem(_make_line(sw, 0, sw, -D - 4, dim_pen))
        _add_text(self._scene, f"{sw:.0f}", sw / 2, -D, dim_font, QColor("#222"))

        # Height arrow left of the sheet
        _arrow_line(self._scene, -D, 0, -D, sh, dim_pen)
        self._scene.addItem(_make_line(0, 0, -D - 4, 0, dim_pen))
        self._scene.addItem(_make_line(0, sh, -D - 4, sh, dim_pen))
        # Rotate height label
        ht = QGraphicsTextItem(f"{sh:.0f}")
        ht.setFont(dim_font)
        ht.setDefaultTextColor(QColor("#222"))
        r = ht.boundingRect()
        ht.setTransformOriginPoint(r.width() / 2, r.height() / 2)
        ht.setRotation(-90)
        ht.setPos(-D - r.height() / 2 - r.width() / 2,
                  sh / 2 + r.width() / 2)
        self._scene.addItem(ht)

        # ── Pieces ────────────────────────────────────────────────────────
        for placement in self._layout.placements:
            x, y = placement.x, placement.y
            pw = placement.placed_width
            ph = placement.placed_height

            color = QColor(placement.piece.color or "#4e79a7")
            color.setAlpha(200)

            rect_item = QGraphicsRectItem(QRectF(x, y, pw, ph))
            rect_item.setBrush(QBrush(color))
            rect_item.setPen(QPen(Qt.GlobalColor.black, 1))
            self._scene.addItem(rect_item)

            # ── Inside label: name (if any) + dimensions ──────────────
            name = placement.piece.label or ""
            rot_mark = " ↻" if placement.rotated else ""
            dim_str = f"{pw:.0f} × {ph:.0f}"
            cx = x + pw / 2
            cy = y + ph / 2

            if name:
                name_font = QFont("Arial", max(6, piece_font_size))
                name_font.setBold(True)
                _add_text(self._scene, name + rot_mark, cx, cy - piece_font_size, name_font)
                _add_text(self._scene, dim_str, cx, cy + piece_font_size, piece_font)
            else:
                _add_text(self._scene, dim_str + rot_mark, cx, cy, piece_font)

        total = self.DIM_OFFSET + self.MARGIN
        self._scene.setSceneRect(-total, -total, sw + 2 * total, sh + 2 * total)
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._layout:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


# ── 1-D canvas ───────────────────────────────────────────────────────────────

class BarCanvas(QGraphicsView):
    """Displays a 1-D bar layout with piece lengths and overall dimension."""

    DIM_OFFSET = 25
    MARGIN = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._layout: BarLayout | None = None

    def set_layout(self, layout: BarLayout) -> None:
        self._layout = layout
        self._draw()

    def _draw(self) -> None:
        self._scene.clear()
        if self._layout is None:
            return

        bar = self._layout.stock
        blen = bar.length
        H = 60.0
        D = self.DIM_OFFSET
        dim_pen = _dim_pen()
        dim_font = QFont("Arial", 8)
        piece_font = QFont("Arial", 8)

        # ── Bar background ────────────────────────────────────────────────
        bg = QGraphicsRectItem(QRectF(0, 0, blen, H))
        bg.setBrush(QBrush(QColor("#f5f5f0")))
        bg.setPen(QPen(QColor("#333"), 2))
        self._scene.addItem(bg)

        # ── Overall length dimension above bar ────────────────────────────
        _arrow_line(self._scene, 0, -D, blen, -D, dim_pen)
        self._scene.addItem(_make_line(0, 0, 0, -D - 4, dim_pen))
        self._scene.addItem(_make_line(blen, 0, blen, -D - 4, dim_pen))
        _add_text(self._scene, f"{blen:.0f}", blen / 2, -D, dim_font, QColor("#222"))

        # ── Pieces ────────────────────────────────────────────────────────
        for pl in self._layout.placements:
            x = pl.offset
            w = pl.piece.length
            color = QColor(pl.piece.color or "#4e79a7")
            color.setAlpha(200)

            rect = QGraphicsRectItem(QRectF(x, 0, w, H))
            rect.setBrush(QBrush(color))
            rect.setPen(QPen(Qt.GlobalColor.black, 1))
            self._scene.addItem(rect)

            # Piece dimension line below bar
            _arrow_line(self._scene, x, H + D * 0.6, x + w, H + D * 0.6, dim_pen)
            self._scene.addItem(_make_line(x, H, x, H + D * 0.6 + 4, dim_pen))
            self._scene.addItem(_make_line(x + w, H, x + w, H + D * 0.6 + 4, dim_pen))

            cx = x + w / 2
            label = pl.piece.label or ""
            if label:
                bold = QFont("Arial", 8)
                bold.setBold(True)
                _add_text(self._scene, label, cx, H / 2 - 8, bold)
            _add_text(self._scene, f"{w:.0f}", cx, H + D * 0.6, dim_font, QColor("#222"))

        total = self.DIM_OFFSET + self.MARGIN
        self._scene.setSceneRect(
            -total, -total,
            blen + 2 * total, H + D + 2 * self.MARGIN
        )
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

