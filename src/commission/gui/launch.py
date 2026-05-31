"""PyInstaller 入口脚本 — 带错误捕获，出错时弹窗提示"""

import sys
import traceback


def main():
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from commission.gui.resources import app_icon
        from commission.gui.styles import build_stylesheet
        from commission.gui.wizard import CommissionWizard

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        icon = app_icon()
        app.setWindowIcon(icon)
        app.setStyleSheet(build_stylesheet())

        win = CommissionWizard()
        win.setWindowIcon(icon)
        win.show()

        sys.exit(app.exec())
    except Exception:
        # 出错时弹出错误对话框，而不是静默退出
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("启动错误")
            msg.setText("程序启动失败，请截图联系开发者：")
            msg.setDetailedText(traceback.format_exc())
            msg.exec()
        except Exception:
            # 如果连 Qt 都加载不了，退回到控制台输出
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
