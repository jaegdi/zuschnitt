"""QGraphicsView-based canvas for displaying one sheet layout."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
)

from zuschnitt.core.models import SheetLayout, BarLayout


class SheetCanvas(QGraphicsView):
    """Displays a 2-D sheet layout with color-coded piece rectangles."""

    MARGIN = 20  # px around the sheet

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

        # Sheet background
        sheet_rect = QRectF(0, 0, sw, sh)
        bg = QGraphicsRectItem(sheet_rect)
        bg.setBrush(QBrush(QColor("#f5f5f0")))
        bg.setPen(QPen(QColor("#333333"), 2))
        self._scene.addItem(bg)

        font = QFont("Arial", max(6, int(min(sw, sh) / 40)))

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

            label = placement.piece.label or f"{pw:.0f}×{ph:.0f}"
            if placement.rotated:
                label += " ↻"
            text = QGraphicsTextItem(label)
            text.setFont(font)
            text.setDefaultTextColor(Qt.GlobalColor.black)
            # Center text in the piece rectangle
            tr = text.boundingRect()
            text.setPos(x + (pw - tr.width()) / 2, y + (ph - tr.height()) / 2)
            self._scene.addItem(text)

        self._scene.setSceneRect(
            -self.MARGIN, -self.MARGIN,
            sw + 2 * self.MARGIN, sh + 2 * self.MARGIN
        )
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._layout:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class BarCanvas(QGraphicsView):
    """Displays a 1-D bar layout."""

    MARGIN = 20

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
        height = 60.0

        bg = QGraphicsRectItem(QRectF(0, 0, blen, height))
        bg.setBrush(QBrush(QColor("#f5f5f0")))
        bg.setPen(QPen(QColor("#333"), 2))
        self._scene.addItem(bg)

        font = QFont("Arial", 8)
        for pl in self._layout.placements:
            x = pl.offset
            w = pl.piece.length
            color = QColor(pl.piece.color or "#4e79a7")
            color.setAlpha(200)
            rect = QGraphicsRectItem(QRectF(x, 0, w, height))
            rect.setBrush(QBrush(color))
            rect.setPen(QPen(Qt.GlobalColor.black, 1))
            self._scene.addItem(rect)
            label = pl.piece.label or f"{w:.0f}"
            text = QGraphicsTextItem(label)
            text.setFont(font)
            tr = text.boundingRect()
            text.setPos(x + (w - tr.width()) / 2, (height - tr.height()) / 2)
            self._scene.addItem(text)

        self._scene.setSceneRect(
            -self.MARGIN, -self.MARGIN,
            blen + 2 * self.MARGIN, height + 2 * self.MARGIN
        )
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
