"""Settings dialog: kerf, units, rotation, grain direction."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QDoubleSpinBox, QComboBox,
    QCheckBox, QDialogButtonBox,
)

from zuschnitt.core.models import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._build_ui(settings)

    def _build_ui(self, s: Settings):
        form = QFormLayout(self)

        self._kerf = QDoubleSpinBox()
        self._kerf.setRange(0, 50)
        self._kerf.setDecimals(1)
        self._kerf.setSuffix(" mm")
        self._kerf.setValue(s.kerf)
        form.addRow("Blade kerf:", self._kerf)

        self._unit = QComboBox()
        self._unit.addItems(["mm", "cm", "inch"])
        self._unit.setCurrentText(s.unit)
        form.addRow("Units:", self._unit)

        self._rotate = QCheckBox("Allow 90° rotation")
        self._rotate.setChecked(s.allow_rotation)
        form.addRow("", self._rotate)

        self._grain = QCheckBox("Respect grain direction (lock rotation)")
        self._grain.setChecked(s.grain_direction)
        form.addRow("", self._grain)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_settings(self) -> Settings:
        return Settings(
            kerf=self._kerf.value(),
            unit=self._unit.currentText(),
            allow_rotation=self._rotate.isChecked(),
            grain_direction=self._grain.isChecked(),
        )
