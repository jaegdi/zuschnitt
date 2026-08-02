"""QGraphicsView-based canvas for displaying one sheet layout."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainter
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsEllipseItem,
)

from zuschnitt.core.models import SheetLayout, BarLayout
from zuschnitt.core.cuts import compute_cuts
from zuschnitt.visualization.cut_label_layout import (
    place_horizontal_cut_markers,
    place_vertical_cut_markers,
)

# ── drawing helpers ──────────────────────────────────────────────────────────

def _add_text(scene, text: str, cx: float, cy: float, font: QFont,
              color: QColor = None) -> QGraphicsTextItem:
    item = QGraphicsTextItem(text)
    item.setFont(font)
    item.setDefaultTextColor(color or Qt.GlobalColor.black)
    r = item.boundingRect()
    item.setPos(cx - r.width() / 2, cy - r.height() / 2)
    scene.addItem(item)
    return item


def _line(scene, x1, y1, x2, y2, pen) -> QGraphicsLineItem:
    item = QGraphicsLineItem(x1, y1, x2, y2)
    item.setPen(pen)
    scene.addItem(item)
    return item


def _arrow(scene, x1, y1, x2, y2, pen, size=8.0):
    _line(scene, x1, y1, x2, y2, pen)
    for ax, ay, bx, by in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
        angle = math.atan2(by - ay, bx - ax)
        for side in (+1, -1):
            lx = ax + size * math.cos(angle + side * math.radians(150))
            ly = ay + size * math.sin(angle + side * math.radians(150))
            _line(scene, ax, ay, lx, ly, pen)


def _dim_pen() -> QPen:
    return QPen(QColor("#444444"), 1)


def _cut_pen() -> QPen:
    pen = QPen(QColor("#c0392b"), 1.5, Qt.PenStyle.DashLine)
    pen.setDashPattern([6, 4])
    return pen


def _circle_label(scene, cx, cy, number: int, radius=10.0, font=None):
    circ = QGraphicsEllipseItem(cx - radius, cy - radius, radius * 2, radius * 2)
    circ.setBrush(QBrush(QColor("#c0392b")))
    circ.setPen(QPen(Qt.GlobalColor.white, 1))
    scene.addItem(circ)
    lbl = QGraphicsTextItem(str(number))
    if font:
        lbl.setFont(font)
    lbl.setDefaultTextColor(Qt.GlobalColor.white)
    r = lbl.boundingRect()
    lbl.setPos(cx - r.width() / 2, cy - r.height() / 2)
    scene.addItem(lbl)


def _leader_line(scene, x1, y1, x2, y2, pen) -> None:
    item = QGraphicsLineItem(x1, y1, x2, y2)
    item.setPen(pen)
    scene.addItem(item)


# ── 2-D canvas ───────────────────────────────────────────────────────────────

class SheetCanvas(QGraphicsView):
    """Displays a 2-D sheet layout with pieces, cut lines, and dimensions."""

    DIM_OFFSET = 30
    MARGIN = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._layout: SheetLayout | None = None
        self._kerf = 0.0

    def set_layout(self, layout: SheetLayout, kerf: float = 0.0) -> None:
        self._layout = layout
        self._kerf = kerf
        self._draw()

    def _draw(self) -> None:
        self._scene.clear()
        if self._layout is None:
            return

        sheet = self._layout.stock
        sw, sh = sheet.width, sheet.height
        D = self.DIM_OFFSET

        pfs = max(6, int(min(sw, sh) / 50))
        piece_font = QFont("Arial", pfs)
        bold_font = QFont("Arial", pfs)
        bold_font.setBold(True)
        dim_font = QFont("Arial", max(5, pfs - 1))
        cut_num_font = QFont("Arial", max(5, pfs - 2))
        dim_pen = _dim_pen()
        cut_pen = _cut_pen()

        # Sheet background
        bg = QGraphicsRectItem(QRectF(0, 0, sw, sh))
        bg.setBrush(QBrush(QColor("#f5f5f0")))
        bg.setPen(QPen(QColor("#333333"), 2))
        self._scene.addItem(bg)

        # Overall width dimension (above)
        _arrow(self._scene, 0, -D, sw, -D, dim_pen)
        _line(self._scene, 0, 0, 0, -D - 4, dim_pen)
        _line(self._scene, sw, 0, sw, -D - 4, dim_pen)
        _add_text(self._scene, f"{sw:.0f}", sw / 2, -D, dim_font, QColor("#222"))

        # Overall height dimension (left, rotated)
        _arrow(self._scene, -D, 0, -D, sh, dim_pen)
        _line(self._scene, 0, 0, -D - 4, 0, dim_pen)
        _line(self._scene, 0, sh, -D - 4, sh, dim_pen)
        ht = QGraphicsTextItem(f"{sh:.0f}")
        ht.setFont(dim_font)
        ht.setDefaultTextColor(QColor("#222"))
        r = ht.boundingRect()
        ht.setTransformOriginPoint(r.width() / 2, r.height() / 2)
        ht.setRotation(-90)
        ht.setPos(-D - r.height() / 2 - r.width() / 2, sh / 2 + r.width() / 2)
        self._scene.addItem(ht)

        # Reference marker (green dot at origin)
        ref = QGraphicsEllipseItem(-5, -5, 10, 10)
        ref.setBrush(QBrush(QColor("#27ae60")))
        ref.setPen(QPen(Qt.GlobalColor.white, 1))
        self._scene.addItem(ref)

        # Pieces
        for placement in self._layout.placements:
            x, y = placement.x, placement.y
            pw, ph = placement.placed_width, placement.placed_height
            color = QColor(placement.piece.color or "#4e79a7")
            color.setAlpha(200)

            rect_item = QGraphicsRectItem(QRectF(x, y, pw, ph))
            rect_item.setBrush(QBrush(color))
            rect_item.setPen(QPen(Qt.GlobalColor.black, 1))
            self._scene.addItem(rect_item)

            name = placement.piece.label or ""
            rot_mark = " ↻" if placement.rotated else ""
            dim_str = f"{pw:.0f} × {ph:.0f}"
            cx, cy = x + pw / 2, y + ph / 2

            if name:
                _add_text(self._scene, name + rot_mark, cx, cy - pfs, bold_font)
                _add_text(self._scene, dim_str, cx, cy + pfs, piece_font)
            else:
                _add_text(self._scene, dim_str + rot_mark, cx, cy, piece_font)

        # Cut lines and numbered circles
        cuts = compute_cuts(self._layout, kerf=self._kerf)
        CIRCLE_R = max(7.0, min(sw, sh) / 55)
        marker_pen = QPen(QColor("#c0392b"), 1)
        h_markers = place_horizontal_cut_markers(
            cuts,
            anchor_x=sw,
            label_x=sw + CIRCLE_R + 18,
            min_sep=CIRCLE_R * 2 + 6,
        )
        v_markers = place_vertical_cut_markers(
            cuts,
            anchor_y=sh,
            label_y=sh + CIRCLE_R + 18,
            min_sep=CIRCLE_R * 2 + 6,
        )

        for cut in cuts:
            if cut.orientation == "H":
                _line(self._scene, 0, cut.position, sw, cut.position, cut_pen)
                _line(self._scene, -D * 0.55, cut.position, 0, cut.position, dim_pen)
                _add_text(self._scene, f"{cut.position:.0f}",
                          -D * 0.55 - 20, cut.position, dim_font, QColor("#555"))
            else:
                _line(self._scene, cut.position, 0, cut.position, sh, cut_pen)
                _line(self._scene, cut.position, -D * 0.55, cut.position, 0, dim_pen)
                _add_text(self._scene, f"{cut.position:.0f}",
                          cut.position, -D * 0.55 - 14, dim_font, QColor("#555"))

        for marker in h_markers:
            _leader_line(
                self._scene,
                marker.anchor_x,
                marker.anchor_y,
                marker.label_x - CIRCLE_R - 2,
                marker.label_y,
                marker_pen,
            )
            _circle_label(self._scene, marker.label_x, marker.label_y,
                          marker.cut.number, CIRCLE_R, cut_num_font)

        for marker in v_markers:
            _leader_line(
                self._scene,
                marker.anchor_x,
                marker.anchor_y,
                marker.label_x,
                marker.label_y - CIRCLE_R - 2,
                marker_pen,
            )
            _circle_label(self._scene, marker.label_x, marker.label_y,
                          marker.cut.number, CIRCLE_R, cut_num_font)

        max_marker_offset = 0.0
        if h_markers:
            max_marker_offset = max(max_marker_offset, max(abs(m.label_y - m.anchor_y) for m in h_markers))
        if v_markers:
            max_marker_offset = max(max_marker_offset, max(abs(m.label_x - m.anchor_x) for m in v_markers))

        total = D + self.MARGIN + CIRCLE_R * 2 + max_marker_offset + 35
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
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
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
        cut_pen = _cut_pen()
        dim_font = QFont("Arial", 8)
        bold_font = QFont("Arial", 8)
        bold_font.setBold(True)
        cut_num_font = QFont("Arial", 7)
        CIRCLE_R = 8.0

        # Bar background
        bg = QGraphicsRectItem(QRectF(0, 0, blen, H))
        bg.setBrush(QBrush(QColor("#f5f5f0")))
        bg.setPen(QPen(QColor("#333"), 2))
        self._scene.addItem(bg)

        # Overall length dimension above
        _arrow(self._scene, 0, -D, blen, -D, dim_pen)
        _line(self._scene, 0, 0, 0, -D - 4, dim_pen)
        _line(self._scene, blen, 0, blen, -D - 4, dim_pen)
        _add_text(self._scene, f"{blen:.0f}", blen / 2, -D, dim_font, QColor("#222"))

        # Reference marker (green dot at left)
        ref = QGraphicsEllipseItem(-5, H / 2 - 5, 10, 10)
        ref.setBrush(QBrush(QColor("#27ae60")))
        ref.setPen(QPen(Qt.GlobalColor.white, 1))
        self._scene.addItem(ref)

        cut_num = 0
        for pl in self._layout.placements:
            x = pl.offset
            w = pl.piece.length
            color = QColor(pl.piece.color or "#4e79a7")
            color.setAlpha(200)

            rect = QGraphicsRectItem(QRectF(x, 0, w, H))
            rect.setBrush(QBrush(color))
            rect.setPen(QPen(Qt.GlobalColor.black, 1))
            self._scene.addItem(rect)

            cx = x + w / 2
            label = pl.piece.label or ""
            if label:
                _add_text(self._scene, label, cx, H / 2 - 8, bold_font)
            _add_text(self._scene, f"{w:.0f}", cx, H / 2 + 4, dim_font)

            # Cut line at right edge (skip sheet boundary)
            cut_x = x + w
            if cut_x < blen - 0.5:
                cut_num += 1
                _line(self._scene, cut_x, 0, cut_x, H, cut_pen)
                _line(self._scene, cut_x, H, cut_x, H + D * 0.6, dim_pen)
                _add_text(self._scene, f"{cut_x:.0f}",
                          cut_x, H + D * 0.6 + 8, dim_font, QColor("#555"))
                _circle_label(self._scene, cut_x, H + D * 0.6 + CIRCLE_R + 18,
                               cut_num, CIRCLE_R, cut_num_font)

        total = D + self.MARGIN + CIRCLE_R * 2 + 30
        self._scene.setSceneRect(
            -total, -total, blen + 2 * total, H + total + D + 30
        )
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
