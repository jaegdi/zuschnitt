"""Editable table panel for stock bars (1-D mode)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
)

from zuschnitt.core.models import StockBar

_COLS = ["Length", "Qty", "Label"]


class BarsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit = "mm"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel("<b>Stock Bars / Rods</b>"))

        self._table = QTableWidget(0, len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self._add_row)
        del_btn = QPushButton("− Remove")
        del_btn.clicked.connect(self._del_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._add_row()

    def _add_row(self):
        row = self._table.rowCount()
        self._table.insertRow(row)
        for col, val in enumerate(["3000", "1", ""]):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, col, item)

    def _del_row(self):
        rows = sorted({i.row() for i in self._table.selectedItems()}, reverse=True)
        for r in rows:
            self._table.removeRow(r)

    def set_unit(self, unit: str):
        self._unit = unit
        self._table.setHorizontalHeaderLabels([f"Length ({unit})", "Qty", "Label"])

    def get_bars(self) -> list[StockBar]:
        bars = []
        for row in range(self._table.rowCount()):
            def cell(col):
                item = self._table.item(row, col)
                return item.text().strip() if item else ""
            try:
                bars.append(StockBar(
                    length=float(cell(0) or 0),
                    quantity=int(cell(1) or 1),
                    label=cell(2),
                ))
            except ValueError:
                pass
        return bars

    def set_bars(self, bars: list[StockBar]):
        self._table.setRowCount(0)
        for b in bars:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([b.length, b.quantity, b.label]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)
