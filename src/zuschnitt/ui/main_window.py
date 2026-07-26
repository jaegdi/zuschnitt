"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QComboBox, QLabel,
    QFileDialog, QMessageBox, QToolBar, QStatusBar, QMenu,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence

from zuschnitt.core.models import Project, Settings
from zuschnitt.core.project import save, load
from zuschnitt.core.optimizer_2d import optimize_2d
from zuschnitt.core.optimizer_1d import optimize_1d
from zuschnitt.ui.sheets_panel import SheetsPanel
from zuschnitt.ui.bars_panel import BarsPanel
from zuschnitt.ui.pieces_panel import PiecesPanel
from zuschnitt.ui.results_panel import ResultsPanel
from zuschnitt.ui.settings_dialog import SettingsDialog
from zuschnitt.visualization.exporter import export_pdf, export_svg

_FILE_FILTER = "Zuschnitt projects (*.zusc);;All files (*)"
_MAX_RECENT = 10


class MainWindow(QMainWindow):
    def __init__(self, open_path: Path | None = None):
        super().__init__()
        self.setWindowTitle("Zuschnitt – Cutting Optimizer")
        self.resize(1200, 750)

        self._project = Project()
        self._current_path: Path | None = None
        self._qsettings = QSettings("Zuschnitt", "Zuschnitt")

        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._update_mode_ui()
        self._rebuild_recent_menu()

        if open_path:
            self._do_open(open_path)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._act(file_menu, "&New", self._new, QKeySequence.StandardKey.New)
        self._act(file_menu, "&Open…", self._open, QKeySequence.StandardKey.Open)

        self._recent_menu = file_menu.addMenu("Open &Recent")

        self._act(file_menu, "&Save", self._save, QKeySequence.StandardKey.Save)
        self._act(file_menu, "Save &As…", self._save_as, QKeySequence.StandardKey.SaveAs)
        file_menu.addSeparator()
        self._act(file_menu, "Export &PDF…", self._export_pdf)
        self._act(file_menu, "Export &SVG…", self._export_svg)
        file_menu.addSeparator()
        self._act(file_menu, "&Quit", self.close, QKeySequence.StandardKey.Quit)

        # Edit
        edit_menu = mb.addMenu("&Edit")
        self._act(edit_menu, "&Settings…", self._open_settings)

        # Help
        help_menu = mb.addMenu("&Help")
        self._act(help_menu, "&About", self._about)

    def _act(self, menu, title, slot, shortcut=None):
        action = QAction(title, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _build_toolbar(self):
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.addWidget(QLabel("  Mode: "))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["2D – Sheets", "1D – Bars/Rods"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_change)
        tb.addWidget(self._mode_combo)

        tb.addSeparator()

        self._optimize_btn = QPushButton("⚙  Optimize")
        self._optimize_btn.setFixedHeight(28)
        self._optimize_btn.clicked.connect(self._optimize)
        tb.addWidget(self._optimize_btn)

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        h = QHBoxLayout(central)
        h.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        h.addWidget(splitter)

        # Left pane: input panels
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)

        self._sheets_panel = SheetsPanel()
        self._bars_panel = BarsPanel()
        self._pieces_panel_2d = PiecesPanel(mode="2d")
        self._pieces_panel_1d = PiecesPanel(mode="1d")

        lv.addWidget(self._sheets_panel)
        lv.addWidget(self._bars_panel)
        lv.addWidget(self._pieces_panel_2d)
        lv.addWidget(self._pieces_panel_1d)

        splitter.addWidget(left)

        # Right pane: results
        self._results = ResultsPanel()
        splitter.addWidget(self._results)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.setStatusBar(QStatusBar())

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def _on_mode_change(self, index: int):
        self._project.mode = "2d" if index == 0 else "1d"
        self._update_mode_ui()

    def _update_mode_ui(self):
        is_2d = self._project.mode == "2d"
        self._sheets_panel.setVisible(is_2d)
        self._pieces_panel_2d.setVisible(is_2d)
        self._bars_panel.setVisible(not is_2d)
        self._pieces_panel_1d.setVisible(not is_2d)
        idx = 0 if is_2d else 1
        self._mode_combo.blockSignals(True)
        self._mode_combo.setCurrentIndex(idx)
        self._mode_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Optimize
    # ------------------------------------------------------------------

    def _optimize(self):
        self._sync_project_from_ui()
        p = self._project
        s = p.settings

        if p.mode == "2d":
            layouts, unplaced = optimize_2d(
                p.sheets, p.pieces_2d,
                kerf=s.kerf,
                allow_rotation=s.allow_rotation,
            )
            p.sheet_layouts = layouts
            self._results.show_2d_results(layouts, len(unplaced))
        else:
            layouts, unplaced = optimize_1d(p.bars, p.pieces_1d, kerf=s.kerf)
            p.bar_layouts = layouts
            self._results.show_1d_results(layouts, len(unplaced))

        status = "Optimization complete."
        if unplaced:
            status += f" {len(unplaced)} piece(s) could not be placed (insufficient stock)."
        self.statusBar().showMessage(status, 5000)

    # ------------------------------------------------------------------
    # Sync UI ↔ project
    # ------------------------------------------------------------------

    def _sync_project_from_ui(self):
        p = self._project
        if p.mode == "2d":
            p.sheets = self._sheets_panel.get_sheets()
            p.pieces_2d = self._pieces_panel_2d.get_pieces_2d()
        else:
            p.bars = self._bars_panel.get_bars()
            p.pieces_1d = self._pieces_panel_1d.get_pieces_1d()

    def _sync_ui_from_project(self):
        p = self._project
        self._mode_combo.setCurrentIndex(0 if p.mode == "2d" else 1)
        self._update_mode_ui()
        unit = p.settings.unit
        self._sheets_panel.set_unit(unit)
        self._bars_panel.set_unit(unit)
        self._pieces_panel_2d.set_unit(unit)
        self._pieces_panel_1d.set_unit(unit)
        self._sheets_panel.set_sheets(p.sheets)
        self._bars_panel.set_bars(p.bars)
        self._pieces_panel_2d.set_pieces_2d(p.pieces_2d)
        self._pieces_panel_1d.set_pieces_1d(p.pieces_1d)

    # ------------------------------------------------------------------
    # Recent files
    # ------------------------------------------------------------------

    def _get_recent(self) -> list[str]:
        val = self._qsettings.value("recentFiles", [])
        if isinstance(val, str):
            val = [val] if val else []
        return list(val) if val else []

    def _add_to_recent(self, path: Path) -> None:
        files = self._get_recent()
        s = str(path.resolve())
        if s in files:
            files.remove(s)
        files.insert(0, s)
        self._qsettings.setValue("recentFiles", files[:_MAX_RECENT])
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        self._recent_menu.clear()
        files = self._get_recent()
        if not files:
            placeholder = QAction("(no recent files)", self)
            placeholder.setEnabled(False)
            self._recent_menu.addAction(placeholder)
            return
        for i, path_str in enumerate(files):
            p = Path(path_str)
            action = QAction(f"&{i+1}  {p.name}  —  {p.parent}", self)
            action.setToolTip(path_str)
            action.setData(path_str)
            action.triggered.connect(self._open_recent)
            self._recent_menu.addAction(action)
        self._recent_menu.addSeparator()
        clear_act = QAction("Clear Recent Files", self)
        clear_act.triggered.connect(self._clear_recent)
        self._recent_menu.addAction(clear_act)

    def _open_recent(self) -> None:
        action = self.sender()
        if action:
            path = Path(action.data())
            if path.exists():
                self._do_open(path)
            else:
                QMessageBox.warning(
                    self, "File not found",
                    f"The file no longer exists:\n{path}"
                )
                files = self._get_recent()
                if str(path) in files:
                    files.remove(str(path))
                self._qsettings.setValue("recentFiles", files)
                self._rebuild_recent_menu()

    def _clear_recent(self) -> None:
        self._qsettings.setValue("recentFiles", [])
        self._rebuild_recent_menu()

    # ------------------------------------------------------------------
    # File actions
    # ------------------------------------------------------------------

    def _new(self):
        self._project = Project()
        self._current_path = None
        self._sync_ui_from_project()
        self.setWindowTitle("Zuschnitt – Cutting Optimizer")

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", _FILE_FILTER)
        if path:
            self._do_open(Path(path))

    def _do_open(self, path: Path):
        try:
            self._project = load(path)
            self._current_path = path
            self._sync_ui_from_project()
            self.setWindowTitle(f"Zuschnitt – {path.name}")
            self._add_to_recent(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")

    def _save(self):
        if self._current_path:
            self._do_save(self._current_path)
        else:
            self._save_as()

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", _FILE_FILTER)
        if path:
            if not path.endswith(".zusc"):
                path += ".zusc"
            self._do_save(Path(path))

    def _do_save(self, path: Path):
        self._sync_project_from_ui()
        try:
            save(self._project, path)
            self._current_path = path
            self.setWindowTitle(f"Zuschnitt – {path.name}")
            self.statusBar().showMessage(f"Saved: {path}", 3000)
            self._add_to_recent(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{e}")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_pdf(self):
        self._sync_project_from_ui()
        p = self._project
        if not (p.sheet_layouts or p.bar_layouts):
            QMessageBox.information(self, "Export", "Run optimization first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF files (*.pdf)")
        if path:
            if not path.endswith(".pdf"):
                path += ".pdf"
            try:
                export_pdf(p, Path(path))
                self.statusBar().showMessage(f"PDF exported: {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"PDF export failed:\n{e}")

    def _export_svg(self):
        self._sync_project_from_ui()
        p = self._project
        if not (p.sheet_layouts or p.bar_layouts):
            QMessageBox.information(self, "Export", "Run optimization first.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Export SVG – select folder")
        if folder:
            try:
                export_svg(p, Path(folder))
                self.statusBar().showMessage(f"SVG exported to: {folder}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"SVG export failed:\n{e}")

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _open_settings(self):
        dlg = SettingsDialog(self._project.settings, self)
        if dlg.exec():
            self._project.settings = dlg.get_settings()
            unit = self._project.settings.unit
            self._sheets_panel.set_unit(unit)
            self._bars_panel.set_unit(unit)
            self._pieces_panel_2d.set_unit(unit)
            self._pieces_panel_1d.set_unit(unit)

    def _about(self):
        QMessageBox.about(
            self, "About Zuschnitt",
            "<h3>Zuschnitt</h3>"
            "<p>A local cutting optimizer for 2-D sheets and 1-D linear stock.</p>"
            "<p>Algorithms: MAXRECTS (2D) &amp; First-Fit Decreasing (1D)</p>"
        )
