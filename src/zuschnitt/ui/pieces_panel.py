"""Editable table panel for pieces to be cut."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QCheckBox,
)

from zuschnitt.core.models import Piece2D, Piece1D
from zuschnitt.utils.colors import get_color

_COLS_2D = ["Width", "Height", "Qty", "Label", "Rotate", "Grain Lock"]
_COLS_1D = ["Length", "Qty", "Label"]


class PiecesPanel(QWidget):
    def __init__(self, mode: str = "2d", parent=None):
        super().__init__(parent)
        self._mode = mode
        self._unit = "mm"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel("<b>Pieces to Cut</b>"))

        cols = _COLS_2D if self._mode == "2d" else _COLS_1D
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
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
        color = get_color(row)

        if self._mode == "2d":
            defaults = ["400", "300", "1", "", True, False]
            for col, val in enumerate(defaults):
                if col in (4, 5):
                    cb = QCheckBox()
                    cb.setChecked(val)
                    cb.setStyleSheet("margin-left: 30%;")
                    self._table.setCellWidget(row, col, cb)
                else:
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col == 0:
                        item.setBackground(QColor(color))
                    self._table.setItem(row, col, item)
        else:
            for col, val in enumerate(["500", "1", ""]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setBackground(QColor(get_color(row)))
                self._table.setItem(row, col, item)

    def _del_row(self):
        rows = sorted({i.row() for i in self._table.selectedItems()}, reverse=True)
        for r in rows:
            self._table.removeRow(r)

    def set_unit(self, unit: str):
        self._unit = unit
        if self._mode == "2d":
            self._table.setHorizontalHeaderLabels(
                [f"Width ({unit})", f"Height ({unit})", "Qty", "Label", "Rotate", "Grain Lock"]
            )
        else:
            self._table.setHorizontalHeaderLabels([f"Length ({unit})", "Qty", "Label"])

    def _cell(self, row: int, col: int) -> str:
        item = self._table.item(row, col)
        return item.text().strip() if item else ""

    def _checked(self, row: int, col: int) -> bool:
        w = self._table.cellWidget(row, col)
        return w.isChecked() if w else False

    def get_pieces_2d(self) -> list[Piece2D]:
        pieces = []
        for row in range(self._table.rowCount()):
            try:
                color = get_color(row)
                pieces.append(Piece2D(
                    width=float(self._cell(row, 0) or 0),
                    height=float(self._cell(row, 1) or 0),
                    quantity=int(self._cell(row, 2) or 1),
                    label=self._cell(row, 3),
                    can_rotate=self._checked(row, 4),
                    grain_locked=self._checked(row, 5),
                    color=color,
                ))
            except ValueError:
                pass
        return pieces

    def get_pieces_1d(self) -> list[Piece1D]:
        pieces = []
        for row in range(self._table.rowCount()):
            try:
                pieces.append(Piece1D(
                    length=float(self._cell(row, 0) or 0),
                    quantity=int(self._cell(row, 1) or 1),
                    label=self._cell(row, 2),
                    color=get_color(row),
                ))
            except ValueError:
                pass
        return pieces

    def set_pieces_2d(self, pieces: list[Piece2D]):
        self._table.setRowCount(0)
        for i, p in enumerate(pieces):
            row = self._table.rowCount()
            self._table.insertRow(row)
            color = p.color or get_color(i)
            for col, val in enumerate([p.width, p.height, p.quantity, p.label]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setBackground(QColor(color))
                self._table.setItem(row, col, item)
            for col, val in enumerate([p.can_rotate, p.grain_locked], start=4):
                cb = QCheckBox()
                cb.setChecked(val)
                cb.setStyleSheet("margin-left: 30%;")
                self._table.setCellWidget(row, col, cb)

    def set_pieces_1d(self, pieces: list[Piece1D]):
        self._table.setRowCount(0)
        for i, p in enumerate(pieces):
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([p.length, p.quantity, p.label]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setBackground(QColor(p.color or get_color(i)))
                self._table.setItem(row, col, item)
