"""Step 5: 结果展示"""

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from commission.calculator import BuyerCommissionResult, SellerCommissionResult
from commission.formatter import format_buyer_result, format_seller_result


class StepResult(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        title = QLabel("查看佣金计算结果")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        subtitle = QLabel("核对 6 步明细后，可复制结果或写入飞书。")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        self.lbl_summary = QLabel("等待计算结果")
        self.lbl_summary.setObjectName("ResultSummary")
        layout.addWidget(self.lbl_summary)

        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setStyleSheet("font-family: 'Consolas', 'Microsoft YaHei', monospace; font-size: 13px;")
        layout.addWidget(self.text_result, 1)

        btn_row = QHBoxLayout()
        self.btn_feishu = QPushButton("写入飞书")
        self.btn_feishu.setObjectName("PrimaryButton")
        self.btn_feishu.setFixedWidth(120)
        self.btn_feishu.clicked.connect(self._write_feishu)
        btn_row.addWidget(self.btn_feishu)

        self.btn_copy = QPushButton("复制结果")
        self.btn_copy.setFixedWidth(120)
        self.btn_copy.clicked.connect(self._copy)
        btn_row.addWidget(self.btn_copy)

        btn_row.addStretch()
        layout.addLayout(btn_row, 0)

        self._result = None
        self._view = ""
        self._property_type = ""
        self._total_amount = 0.0

    def validate(self) -> bool:
        return True

    def show_result(self, result: BuyerCommissionResult | SellerCommissionResult,
                    view: str = "", property_type: str = "", total_amount: float = 0.0) -> None:
        self._result = result
        self._view = view
        self._property_type = property_type
        self._total_amount = total_amount
        view_label = "成交人" if view == "buyer" else "房源方"
        self.lbl_summary.setText(
            f"{view_label} · 总额 {total_amount:,.2f} 元 · "
            f"进店 {result.store_income:,.2f} 元 · 应发 {result.agent_commission:,.2f} 元"
        )
        if isinstance(result, BuyerCommissionResult):
            self.text_result.setPlainText(format_buyer_result(result))
        else:
            self.text_result.setPlainText(format_seller_result(result))

    def _copy(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_result.toPlainText())

    def _write_feishu(self) -> None:
        if not self._result:
            return
        try:
            from commission.feishu import write_to_feishu
            from commission.records import extract_records
            records = extract_records(self._result, self._view, self._property_type, self._total_amount)
            if not records:
                QMessageBox.warning(self, "提示", "没有可写入的记录")
                return
            url = write_to_feishu(records)
            QMessageBox.information(self, "写入成功", f"已写入飞书多维表格：\n{url}")
        except Exception as e:
            QMessageBox.critical(self, "写入失败", f"写入飞书多维表格失败：\n{e}")
