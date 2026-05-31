from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def app_icon() -> QIcon:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    return QIcon(str(base_dir / "assets" / "app.ico"))
