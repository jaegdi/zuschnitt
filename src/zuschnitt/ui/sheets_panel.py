"""Editable table panel for stock sheets (2-D mode)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
)

from zuschnitt.core.models import StockSheet

_COLS = ["Width", "Height", "Qty", "Label"]


class SheetsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit = "mm"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel("<b>Stock Sheets</b>"))

        self._table = QTableWidget(0, len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        hh = self._table.horizontalHeader()
        # Width, Height: fixed narrow; Qty: fixed narrow; Label: stretches
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.resizeSection(0, 80)
        hh.resizeSection(1, 80)
        hh.resizeSection(2, 50)
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

        self._add_row()  # start with one empty row

    def _add_row(self):
        row = self._table.rowCount()
        self._table.insertRow(row)
        defaults = ["1000", "500", "1", ""]
        for col, val in enumerate(defaults):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, col, item)

    def _del_row(self):
        rows = sorted({i.row() for i in self._table.selectedItems()}, reverse=True)
        for r in rows:
            self._table.removeRow(r)

    def set_unit(self, unit: str):
        self._unit = unit
        self._table.setHorizontalHeaderLabels(
            [f"Width ({unit})", f"Height ({unit})", "Qty", "Label"]
        )

    def get_sheets(self) -> list[StockSheet]:
        sheets = []
        for row in range(self._table.rowCount()):
            def cell(col):
                item = self._table.item(row, col)
                return item.text().strip() if item else ""
            try:
                sheets.append(StockSheet(
                    width=float(cell(0) or 0),
                    height=float(cell(1) or 0),
                    quantity=int(cell(2) or 1),
                    label=cell(3),
                ))
            except ValueError:
                pass
        return sheets

    def set_sheets(self, sheets: list[StockSheet]):
        self._table.setRowCount(0)
        for s in sheets:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([s.width, s.height, s.quantity, s.label]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)
