"""佣金计算器 GUI 入口"""

import sys

from PySide6.QtWidgets import QApplication

from commission.gui.resources import app_icon
from commission.gui.styles import build_stylesheet
from commission.gui.wizard import CommissionWizard


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon = app_icon()
    app.setWindowIcon(icon)
    app.setStyleSheet(build_stylesheet())

    win = CommissionWizard()
    win.setWindowIcon(icon)
    win.show()

    sys.exit(app.exec())
