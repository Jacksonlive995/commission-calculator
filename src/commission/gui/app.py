"""佣金计算器 GUI 入口"""

import sys

from PySide6.QtWidgets import QApplication

from commission.gui.wizard import CommissionWizard


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = CommissionWizard()
    win.show()

    sys.exit(app.exec())
