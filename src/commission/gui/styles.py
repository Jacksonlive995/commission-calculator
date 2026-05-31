from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QMainWindow {
        background: #f5f7fb;
    }
    QWidget {
        color: #1f2937;
        font-size: 13px;
    }
    QLabel#PageTitle {
        font-size: 18px;
        font-weight: 600;
        color: #111827;
    }
    QLabel#PageSubtitle {
        color: #6b7280;
    }
    QLabel#SectionTitle {
        font-weight: 600;
        color: #374151;
        margin-top: 8px;
    }
    QLabel#ResultSummary {
        padding: 12px 14px;
        border-radius: 10px;
        background: #eff6ff;
        color: #1d4ed8;
        font-weight: 600;
    }
    QFrame#Card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
    }
    QPushButton {
        min-height: 36px;
        border-radius: 8px;
        padding: 6px 14px;
        background: #ffffff;
        border: 1px solid #d1d5db;
    }
    QPushButton:hover {
        background: #f9fafb;
    }
    QPushButton#PrimaryButton {
        background: #2563eb;
        color: white;
        border: none;
    }
    QPushButton#PrimaryButton:hover {
        background: #1d4ed8;
    }
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {
        min-height: 34px;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 6px 10px;
        background: white;
    }
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
        border: 1px solid #2563eb;
    }
    """
