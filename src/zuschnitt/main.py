"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from zuschnitt.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Zuschnitt")
    app.setOrganizationName("Zuschnitt")

    open_path: Path | None = None
    args = sys.argv[1:]
    if "--open" in args:
        idx = args.index("--open")
        if idx + 1 < len(args):
            open_path = Path(args[idx + 1])
    elif args and not args[0].startswith("-"):
        open_path = Path(args[0])

    window = MainWindow(open_path=open_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
