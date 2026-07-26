"""Results panel: tabbed view of sheet/bar layouts with summary."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QSplitter,
)
from PySide6.QtCore import Qt

from zuschnitt.core.models import SheetLayout, BarLayout
from zuschnitt.visualization.sheet_canvas import SheetCanvas, BarCanvas


class ResultsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self._summary = QLabel("No results yet. Add sheets and pieces, then click Optimize.")
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

    def show_2d_results(self, layouts: list[SheetLayout], unplaced_count: int):
        self._tabs.clear()
        if not layouts:
            self._summary.setText("No pieces could be placed.")
            return

        total_pieces = sum(len(l.placements) for l in layouts)
        total_waste_pct = (
            sum(l.waste_pct() for l in layouts) / len(layouts)
        )
        self._summary.setText(
            f"<b>{len(layouts)}</b> sheet(s) used &nbsp;|&nbsp; "
            f"<b>{total_pieces}</b> pieces placed &nbsp;|&nbsp; "
            f"Avg waste: <b>{total_waste_pct:.1f}%</b>"
            + (f" &nbsp;|&nbsp; <b style='color:red'>{unplaced_count} unplaced</b>" if unplaced_count else "")
        )

        for i, layout in enumerate(layouts):
            canvas = SheetCanvas()
            canvas.set_layout(layout)
            stock = layout.stock
            tab_label = (
                f"Sheet {i+1}"
                + (f" – {stock.label}" if stock.label else "")
                + f" ({layout.waste_pct():.1f}% waste)"
            )
            self._tabs.addTab(canvas, tab_label)

    def show_1d_results(self, layouts: list[BarLayout], unplaced_count: int):
        self._tabs.clear()
        if not layouts:
            self._summary.setText("No pieces could be placed.")
            return

        total_pieces = sum(len(l.placements) for l in layouts)
        total_waste_pct = (
            sum(l.waste_pct() for l in layouts) / len(layouts)
        )
        self._summary.setText(
            f"<b>{len(layouts)}</b> bar(s) used &nbsp;|&nbsp; "
            f"<b>{total_pieces}</b> pieces placed &nbsp;|&nbsp; "
            f"Avg waste: <b>{total_waste_pct:.1f}%</b>"
            + (f" &nbsp;|&nbsp; <b style='color:red'>{unplaced_count} unplaced</b>" if unplaced_count else "")
        )

        for i, layout in enumerate(layouts):
            canvas = BarCanvas()
            canvas.set_layout(layout)
            tab_label = (
                f"Bar {i+1}"
                + (f" – {layout.stock.label}" if layout.stock.label else "")
                + f" ({layout.waste_pct():.1f}% waste)"
            )
            self._tabs.addTab(canvas, tab_label)
