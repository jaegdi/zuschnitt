"""Zuschnitt Android – Kivy-based cutting optimizer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow imports from the android/ folder itself
sys.path.insert(0, os.path.dirname(__file__))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

from core.models import Project, Settings, StockSheet, StockBar, Piece2D, Piece1D
from core.optimizer_2d import optimize_2d
from core.optimizer_1d import optimize_1d
from core.project import save, load
from sheet_widget import SheetWidget
from utils.colors import get_color

# ── colour palette ────────────────────────────────────────────────────────────
BG   = get_color_from_hex("#1e1e2e")
CARD = get_color_from_hex("#2a2a3e")
ACCENT = get_color_from_hex("#4e79a7")
RED  = get_color_from_hex("#c0392b")
GREEN = get_color_from_hex("#27ae60")
FG   = get_color_from_hex("#e0e0e0")

# ── shared state ──────────────────────────────────────────────────────────────
APP_STATE = {
    "project": Project(),
    "current_path": None,
}


def _btn(text, callback, bg=None, height=dp(48)):
    b = Button(
        text=text, size_hint_y=None, height=height,
        background_color=bg or ACCENT,
        color=FG, bold=True,
    )
    b.bind(on_press=callback)
    return b


def _lbl(text, size=14, bold=False, color=None):
    return Label(
        text=text, font_size=dp(size), bold=bold,
        color=color or FG, size_hint_y=None, height=dp(size + 10),
    )


def _inp(hint="", text="", width=None):
    kw = dict(
        hint_text=hint, text=str(text),
        background_color=CARD, foreground_color=FG,
        cursor_color=FG, font_size=dp(14),
        size_hint_y=None, height=dp(40),
        multiline=False,
    )
    if width:
        kw["size_hint_x"] = None
        kw["width"] = width
    return TextInput(**kw)


# ── Row widgets ───────────────────────────────────────────────────────────────

class SheetRow(BoxLayout):
    def __init__(self, width=1000, height=500, qty=1, label="", **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None,
                         height=dp(44), spacing=dp(4), **kwargs)
        self.t_w = _inp("Width", width)
        self.t_h = _inp("Height", height)
        self.t_q = _inp("Qty", qty, width=dp(55))
        self.t_l = _inp("Label", label)
        rm = Button(text="✕", size_hint_x=None, width=dp(40),
                    background_color=RED, color=FG, font_size=dp(14))
        rm.bind(on_press=lambda *_: self.parent.remove_widget(self))
        for w in [self.t_w, self.t_h, self.t_q, self.t_l, rm]:
            self.add_widget(w)

    def get_sheet(self):
        return StockSheet(
            width=float(self.t_w.text or 1000),
            height=float(self.t_h.text or 500),
            quantity=int(self.t_q.text or 1),
            label=self.t_l.text,
        )


class BarRow(BoxLayout):
    def __init__(self, length=3000, qty=1, label="", **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None,
                         height=dp(44), spacing=dp(4), **kwargs)
        self.t_l = _inp("Length", length)
        self.t_q = _inp("Qty", qty, width=dp(55))
        self.t_n = _inp("Label", label)
        rm = Button(text="✕", size_hint_x=None, width=dp(40),
                    background_color=RED, color=FG, font_size=dp(14))
        rm.bind(on_press=lambda *_: self.parent.remove_widget(self))
        for w in [self.t_l, self.t_q, self.t_n, rm]:
            self.add_widget(w)

    def get_bar(self):
        return StockBar(
            length=float(self.t_l.text or 3000),
            quantity=int(self.t_q.text or 1),
            label=self.t_n.text,
        )


class Piece2DRow(BoxLayout):
    def __init__(self, idx=0, width=400, height=300, qty=1, label="", **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None,
                         height=dp(44), spacing=dp(4), **kwargs)
        self._color = get_color(idx)
        self.t_w = _inp("W", width)
        self.t_h = _inp("H", height)
        self.t_q = _inp("Qty", qty, width=dp(55))
        self.t_l = _inp("Label", label)
        rm = Button(text="✕", size_hint_x=None, width=dp(40),
                    background_color=RED, color=FG, font_size=dp(14))
        rm.bind(on_press=lambda *_: self.parent.remove_widget(self))
        for w in [self.t_w, self.t_h, self.t_q, self.t_l, rm]:
            self.add_widget(w)

    def get_piece(self):
        return Piece2D(
            width=float(self.t_w.text or 400),
            height=float(self.t_h.text or 300),
            quantity=int(self.t_q.text or 1),
            label=self.t_l.text,
            color=self._color,
        )


class Piece1DRow(BoxLayout):
    def __init__(self, idx=0, length=500, qty=1, label="", **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None,
                         height=dp(44), spacing=dp(4), **kwargs)
        self._color = get_color(idx)
        self.t_l = _inp("Length", length)
        self.t_q = _inp("Qty", qty, width=dp(55))
        self.t_n = _inp("Label", label)
        rm = Button(text="✕", size_hint_x=None, width=dp(40),
                    background_color=RED, color=FG, font_size=dp(14))
        rm.bind(on_press=lambda *_: self.parent.remove_widget(self))
        for w in [self.t_l, self.t_q, self.t_n, rm]:
            self.add_widget(w)

    def get_piece(self):
        return Piece1D(
            length=float(self.t_l.text or 500),
            quantity=int(self.t_q.text or 1),
            label=self.t_n.text,
            color=self._color,
        )


# ── Screens ───────────────────────────────────────────────────────────────────

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(16))
        root.add_widget(_lbl("✂  Zuschnitt", size=24, bold=True, color=ACCENT))
        root.add_widget(_lbl("Cutting Optimizer", size=14, color=FG))

        root.add_widget(Label(size_hint_y=1))  # spacer

        root.add_widget(_btn("2D – Sheet Cutting", self._go_2d, height=dp(60)))
        root.add_widget(_btn("1D – Bar / Rod Cutting", self._go_1d, height=dp(60)))
        root.add_widget(Label(size_hint_y=None, height=dp(20)))
        root.add_widget(_btn("⚙  Settings", self._go_settings, bg=CARD))
        root.add_widget(_btn("📂  Open / Save Project", self._go_file, bg=CARD))

        root.add_widget(Label(size_hint_y=1))
        self.add_widget(root)

    def _go_2d(self, *_):
        APP_STATE["project"].mode = "2d"
        self.manager.current = "input"

    def _go_1d(self, *_):
        APP_STATE["project"].mode = "1d"
        self.manager.current = "input"

    def _go_settings(self, *_):
        self.manager.current = "settings"

    def _go_file(self, *_):
        self.manager.current = "file"


class InputScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stock_rows = []
        self._piece_rows = []
        self._build()

    def _build(self):
        self.clear_widgets()
        p = APP_STATE["project"]
        mode = p.mode
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        back = Button(text="← Back", size_hint_x=None, width=dp(80),
                      background_color=CARD, color=FG)
        back.bind(on_press=lambda *_: setattr(self.manager, "current", "main"))
        hdr.add_widget(back)
        title = "2D – Sheets" if mode == "2d" else "1D – Bars"
        hdr.add_widget(_lbl(title, size=16, bold=True))
        root.add_widget(hdr)

        # Stock section
        stock_lbl = "Stock Sheets" if mode == "2d" else "Stock Bars / Rods"
        root.add_widget(_lbl(f"  {stock_lbl}", bold=True, color=ACCENT))

        col_hdr = self._col_header(
            ["Width", "Height", "Qty", "Label", ""] if mode == "2d"
            else ["Length", "Qty", "Label", ""]
        )
        root.add_widget(col_hdr)

        self._stock_container = GridLayout(
            cols=1, size_hint_y=None, spacing=dp(2)
        )
        self._stock_container.bind(
            minimum_height=self._stock_container.setter("height")
        )
        stock_scroll = ScrollView(size_hint_y=None, height=dp(160))
        stock_scroll.add_widget(self._stock_container)
        root.add_widget(stock_scroll)

        add_stock = _btn(f"+ Add {stock_lbl}", self._add_stock,
                         bg=GREEN, height=dp(38))
        root.add_widget(add_stock)

        # Pieces section
        root.add_widget(_lbl("  Pieces to Cut", bold=True, color=ACCENT))
        piece_col = (
            ["Width", "Height", "Qty", "Label", ""] if mode == "2d"
            else ["Length", "Qty", "Label", ""]
        )
        root.add_widget(self._col_header(piece_col))

        self._piece_container = GridLayout(
            cols=1, size_hint_y=None, spacing=dp(2)
        )
        self._piece_container.bind(
            minimum_height=self._piece_container.setter("height")
        )
        piece_scroll = ScrollView(size_hint_y=None, height=dp(200))
        piece_scroll.add_widget(self._piece_container)
        root.add_widget(piece_scroll)

        add_piece = _btn("+ Add Piece", self._add_piece, bg=GREEN, height=dp(38))
        root.add_widget(add_piece)

        root.add_widget(Label(size_hint_y=1))

        optimize_btn = _btn("⚙  Optimize", self._optimize, height=dp(56))
        root.add_widget(optimize_btn)

        self.add_widget(root)

        # Pre-populate from project
        self._load_from_project()

    def _col_header(self, labels):
        row = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(4))
        for l in labels:
            row.add_widget(Label(text=l, font_size=dp(11), color=ACCENT,
                                 bold=True, size_hint_x=None,
                                 width=dp(40) if l == "" else None))
        return row

    def on_pre_enter(self):
        self._build()

    def _load_from_project(self):
        p = APP_STATE["project"]
        self._stock_container.clear_widgets()
        self._piece_container.clear_widgets()
        if p.mode == "2d":
            for s in (p.sheets or [StockSheet(1000, 500)]):
                row = SheetRow(s.width, s.height, s.quantity, s.label)
                self._stock_container.add_widget(row)
            for i, pc in enumerate(p.pieces_2d or [Piece2D(400, 300)]):
                row = Piece2DRow(i, pc.width, pc.height, pc.quantity, pc.label)
                self._piece_container.add_widget(row)
        else:
            for b in (p.bars or [StockBar(3000)]):
                row = BarRow(b.length, b.quantity, b.label)
                self._stock_container.add_widget(row)
            for i, pc in enumerate(p.pieces_1d or [Piece1D(500)]):
                row = Piece1DRow(i, pc.length, pc.quantity, pc.label)
                self._piece_container.add_widget(row)

    def _add_stock(self, *_):
        p = APP_STATE["project"]
        if p.mode == "2d":
            self._stock_container.add_widget(SheetRow())
        else:
            self._stock_container.add_widget(BarRow())

    def _add_piece(self, *_):
        p = APP_STATE["project"]
        idx = len(self._piece_container.children)
        if p.mode == "2d":
            self._piece_container.add_widget(Piece2DRow(idx))
        else:
            self._piece_container.add_widget(Piece1DRow(idx))

    def _sync_to_project(self):
        p = APP_STATE["project"]
        s = p.settings
        if p.mode == "2d":
            p.sheets = [
                w.get_sheet() for w in reversed(self._stock_container.children)
                if isinstance(w, SheetRow)
            ]
            p.pieces_2d = [
                w.get_piece() for w in reversed(self._piece_container.children)
                if isinstance(w, Piece2DRow)
            ]
        else:
            p.bars = [
                w.get_bar() for w in reversed(self._stock_container.children)
                if isinstance(w, BarRow)
            ]
            p.pieces_1d = [
                w.get_piece() for w in reversed(self._piece_container.children)
                if isinstance(w, Piece1DRow)
            ]

    def _optimize(self, *_):
        self._sync_to_project()
        p = APP_STATE["project"]
        s = p.settings
        if p.mode == "2d":
            layouts, unplaced = optimize_2d(
                p.sheets, p.pieces_2d, kerf=s.kerf, allow_rotation=s.allow_rotation
            )
            p.sheet_layouts = layouts
        else:
            layouts, unplaced = optimize_1d(p.bars, p.pieces_1d, kerf=s.kerf)
            p.bar_layouts = layouts

        if not layouts:
            self._popup("No results", "No pieces could be placed.\nCheck stock sizes.")
            return
        msg = f"{len(layouts)} stock unit(s) used."
        if unplaced:
            msg += f"\n{len(unplaced)} piece(s) could not be placed."
        self._popup("Done!", msg, on_dismiss=self._go_results)

    def _go_results(self, *_):
        self.manager.current = "results"

    def _popup(self, title, msg, on_dismiss=None):
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text=msg, color=FG))
        btn = Button(text="OK", size_hint_y=None, height=dp(44),
                     background_color=ACCENT, color=FG)
        content.add_widget(btn)
        pop = Popup(title=title, content=content,
                    size_hint=(0.8, 0.4), background_color=CARD)
        btn.bind(on_press=pop.dismiss)
        if on_dismiss:
            pop.bind(on_dismiss=lambda *_: on_dismiss())
        pop.open()


class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self):
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        hdr = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        back = Button(text="← Back", size_hint_x=None, width=dp(80),
                      background_color=CARD, color=FG)
        back.bind(on_press=lambda *_: setattr(self.manager, "current", "input"))
        hdr.add_widget(back)
        hdr.add_widget(_lbl("Results", size=16, bold=True))
        export_btn = Button(text="⬇ Export PDF", size_hint_x=None, width=dp(130),
                            background_color=GREEN, color=FG, bold=True)
        export_btn.bind(on_press=self._export_pdf)
        hdr.add_widget(export_btn)
        root.add_widget(hdr)

        p = APP_STATE["project"]
        layouts = p.sheet_layouts if p.mode == "2d" else p.bar_layouts
        if not layouts:
            root.add_widget(Label(text="No results yet.\nRun Optimize first.", color=FG))
            self.add_widget(root)
            return

        # Summary
        total = sum(len(l.placements) for l in layouts)
        avg_waste = sum(l.waste_pct() for l in layouts) / len(layouts)
        root.add_widget(_lbl(
            f"{len(layouts)} sheet(s) used  |  {total} pieces  |  "
            f"Avg waste: {avg_waste:.1f}%",
            color=ACCENT
        ))

        # Tabs (simple button row)
        tab_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        self._tab_buttons = []
        for i in range(len(layouts)):
            lbl = f"#{i+1} ({layouts[i].waste_pct():.0f}%w)"
            btn = ToggleButton(text=lbl, group="tabs",
                               background_color=CARD, color=FG,
                               font_size=dp(12))
            btn.bind(on_press=lambda b, idx=i: self._show_tab(idx))
            tab_bar.add_widget(btn)
            self._tab_buttons.append(btn)
        root.add_widget(tab_bar)

        # Canvas area
        self._canvas_area = BoxLayout()
        root.add_widget(self._canvas_area)

        self.add_widget(root)
        self._layouts = layouts
        if self._tab_buttons:
            self._tab_buttons[0].state = "down"
            self._show_tab(0)

    def _show_tab(self, idx):
        self._canvas_area.clear_widgets()
        p = APP_STATE["project"]
        if p.mode == "2d":
            w = SheetWidget(self._layouts[idx])
        else:
            # For 1D, show a simple text summary
            layout = self._layouts[idx]
            box = BoxLayout(orientation="vertical", padding=dp(8))
            box.add_widget(_lbl(f"Bar length: {layout.stock.length:.0f} mm", bold=True))
            box.add_widget(_lbl(f"Waste: {layout.waste_pct():.1f}%"))
            for pl in layout.placements:
                box.add_widget(_lbl(
                    f"  {pl.piece.label or 'piece'}: {pl.piece.length:.0f} mm @ {pl.offset:.0f} mm"
                ))
            w = ScrollView()
            w.add_widget(box)
        self._canvas_area.add_widget(w)

    def _export_pdf(self, *_):
        try:
            from visualization_export import export_pdf_android
            p = APP_STATE["project"]
            name = APP_STATE.get("current_path")
            if name:
                stem = Path(name).stem
            else:
                stem = p.name or "cutting_plan"
            out_dir = Path("/sdcard/Download")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{stem}.pdf"
            export_pdf_android(p, out_path)
            self._popup_msg("PDF Exported", f"Saved to:\n{out_path}")
        except Exception as e:
            self._popup_msg("Export Error", str(e))

    def _popup_msg(self, title, msg):
        content = BoxLayout(orientation="vertical", padding=dp(12))
        content.add_widget(Label(text=msg, color=FG))
        btn = Button(text="OK", size_hint_y=None, height=dp(44),
                     background_color=ACCENT, color=FG)
        pop = Popup(title=title, content=content,
                    size_hint=(0.85, 0.4), background_color=CARD)
        btn.bind(on_press=pop.dismiss)
        content.add_widget(btn)
        pop.open()


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        self.clear_widgets()
        p = APP_STATE["project"]
        s = p.settings
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        hdr = BoxLayout(size_hint_y=None, height=dp(48))
        back = Button(text="← Back", size_hint_x=None, width=dp(80),
                      background_color=CARD, color=FG)
        back.bind(on_press=self._save_and_back)
        hdr.add_widget(back)
        hdr.add_widget(_lbl("Settings", size=16, bold=True))
        root.add_widget(hdr)

        root.add_widget(_lbl("Saw blade kerf (mm):", bold=True))
        self._kerf = _inp("kerf mm", s.kerf)
        root.add_widget(self._kerf)

        root.add_widget(_lbl("Units:", bold=True))
        self._unit = Spinner(
            text=s.unit, values=["mm", "cm", "inch"],
            size_hint_y=None, height=dp(44),
            background_color=CARD, color=FG,
        )
        root.add_widget(self._unit)

        self._rotate = ToggleButton(
            text="Allow 90° Rotation",
            state="down" if s.allow_rotation else "normal",
            size_hint_y=None, height=dp(44),
            background_color=ACCENT if s.allow_rotation else CARD,
            color=FG,
        )
        root.add_widget(self._rotate)

        root.add_widget(Label(size_hint_y=1))
        root.add_widget(_btn("Save Settings", self._save_and_back))
        self.add_widget(root)

    def on_pre_enter(self):
        self._build()

    def _save_and_back(self, *_):
        s = APP_STATE["project"].settings
        try:
            s.kerf = float(self._kerf.text or 3)
        except ValueError:
            pass
        s.unit = self._unit.text
        s.allow_rotation = self._rotate.state == "down"
        self.manager.current = "main"


class FileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        hdr = BoxLayout(size_hint_y=None, height=dp(48))
        back = Button(text="← Back", size_hint_x=None, width=dp(80),
                      background_color=CARD, color=FG)
        back.bind(on_press=lambda *_: setattr(self.manager, "current", "main"))
        hdr.add_widget(back)
        hdr.add_widget(_lbl("Open / Save Project", size=15, bold=True))
        root.add_widget(hdr)

        self._fc = FileChooserListView(
            path=str(Path.home()),
            filters=["*.zusc", "*.ZUSC"],
        )
        root.add_widget(self._fc)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        btn_row.add_widget(_btn("📂 Open", self._open_file, bg=ACCENT))
        btn_row.add_widget(_btn("💾 Save", self._save_file, bg=GREEN))
        root.add_widget(btn_row)
        self.add_widget(root)

    def on_pre_enter(self):
        self._build()

    def _open_file(self, *_):
        sel = self._fc.selection
        if not sel:
            return
        path = Path(sel[0])
        try:
            APP_STATE["project"] = load(path)
            APP_STATE["current_path"] = str(path)
            self._popup_msg("Opened", f"Loaded:\n{path.name}")
            self.manager.current = "main"
        except Exception as e:
            self._popup_msg("Error", str(e))

    def _save_file(self, *_):
        path = self._fc.path
        p = APP_STATE["project"]
        name = (APP_STATE.get("current_path") and
                Path(APP_STATE["current_path"]).stem) or p.name or "project"
        out = Path(path) / f"{name}.zusc"
        try:
            save(p, out)
            APP_STATE["current_path"] = str(out)
            self._popup_msg("Saved", f"Saved to:\n{out.name}")
        except Exception as e:
            self._popup_msg("Error", str(e))

    def _popup_msg(self, title, msg):
        content = BoxLayout(orientation="vertical", padding=dp(12))
        content.add_widget(Label(text=msg, color=FG))
        btn = Button(text="OK", size_hint_y=None, height=dp(44),
                     background_color=ACCENT, color=FG)
        pop = Popup(title=title, content=content,
                    size_hint=(0.85, 0.4), background_color=CARD)
        btn.bind(on_press=pop.dismiss)
        content.add_widget(btn)
        pop.open()


# ── App ───────────────────────────────────────────────────────────────────────

class ZuschnittApp(App):
    def build(self):
        Window.clearcolor = BG
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(InputScreen(name="input"))
        sm.add_widget(ResultsScreen(name="results"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(FileScreen(name="file"))
        return sm


if __name__ == "__main__":
    ZuschnittApp().run()
