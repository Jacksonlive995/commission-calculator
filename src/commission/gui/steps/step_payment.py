"""Step 2: 支付信息"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from commission.config import PAYMENT_OPTIONS, PAYMENT_RATES


class StepPayment(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._is_buyer = True
        self._init_ui()

    def _init_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(10)

        title = QLabel("输入支付金额和平台费")
        title.setObjectName("PageTitle")
        self._layout.addWidget(title)

        subtitle = QLabel("根据成交人或房源方视角录入支付信息。")
        subtitle.setObjectName("PageSubtitle")
        self._layout.addWidget(subtitle)
        self._layout.addSpacing(12)

        # 成交人视角：业主 + 客户
        self.buyer_widget = QWidget()
        bl = QFormLayout(self.buyer_widget)
        bl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        bl.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        self.sp_owner = QDoubleSpinBox()
        self.sp_owner.setRange(0.01, 9999999)
        self.sp_owner.setDecimals(2)
        self.sp_owner.setPrefix("¥ ")
        self.cb_owner = QComboBox()
        self.cb_owner.addItems(PAYMENT_OPTIONS)
        self.lbl_owner_fee = QLabel("¥ 0.00")
        self.lbl_owner_fee.setStyleSheet("color:#666;")
        bl.addRow("业主支付佣金：", self.sp_owner)
        bl.addRow("支付方式：", self.cb_owner)
        bl.addRow("平台费预览：", self.lbl_owner_fee)

        self.sp_customer = QDoubleSpinBox()
        self.sp_customer.setRange(0.01, 9999999)
        self.sp_customer.setDecimals(2)
        self.sp_customer.setPrefix("¥ ")
        self.cb_customer = QComboBox()
        self.cb_customer.addItems(PAYMENT_OPTIONS)
        self.lbl_customer_fee = QLabel("¥ 0.00")
        self.lbl_customer_fee.setStyleSheet("color:#666;")
        bl.addRow("客户支付佣金：", self.sp_customer)
        bl.addRow("支付方式：", self.cb_customer)
        bl.addRow("平台费预览：", self.lbl_customer_fee)

        self.lbl_total_fee = QLabel()
        self.lbl_total_fee.setStyleSheet("font-weight:bold; color:#333;")
        bl.addRow("合计平台费：", self.lbl_total_fee)

        # 房源方视角：总额
        self.seller_widget = QWidget()
        sl = QFormLayout(self.seller_widget)
        sl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.sp_total = QDoubleSpinBox()
        self.sp_total.setRange(0.01, 9999999)
        self.sp_total.setDecimals(2)
        self.sp_total.setPrefix("¥ ")
        sl.addRow("对方收佣金合计：", self.sp_total)

        self._layout.addWidget(self.buyer_widget)
        self._layout.addWidget(self.seller_widget)
        self._layout.addStretch()

        # 实时预览
        self.sp_owner.valueChanged.connect(self._update_preview)
        self.cb_owner.currentIndexChanged.connect(self._update_preview)
        self.sp_customer.valueChanged.connect(self._update_preview)
        self.cb_customer.currentIndexChanged.connect(self._update_preview)

    def setup(self, type_state: dict) -> None:
        self._is_buyer = type_state["view"] == "buyer"
        self.buyer_widget.setVisible(self._is_buyer)
        self.seller_widget.setVisible(not self._is_buyer)
        self._update_preview()

    def _update_preview(self) -> None:
        if self._is_buyer:
            owner_rate = PAYMENT_RATES[PAYMENT_OPTIONS[self.cb_owner.currentIndex()]]
            customer_rate = PAYMENT_RATES[PAYMENT_OPTIONS[self.cb_customer.currentIndex()]]
            of = self.sp_owner.value() * owner_rate
            cf = self.sp_customer.value() * customer_rate
            self.lbl_owner_fee.setText(f"¥ {of:,.2f}")
            self.lbl_customer_fee.setText(f"¥ {cf:,.2f}")
            self.lbl_total_fee.setText(f"¥ {of + cf:,.2f}")

    def validate(self) -> bool:
        if self._is_buyer:
            if self.sp_owner.value() <= 0:
                return False
            if self.sp_customer.value() <= 0:
                return False
        else:
            if self.sp_total.value() <= 0:
                return False
        return True

    def get_state(self) -> dict:
        if self._is_buyer:
            return {
                "owner_amount": self.sp_owner.value(),
                "owner_method": PAYMENT_OPTIONS[self.cb_owner.currentIndex()],
                "customer_amount": self.sp_customer.value(),
                "customer_method": PAYMENT_OPTIONS[self.cb_customer.currentIndex()],
            }
        return {
            "total_amount": self.sp_total.value(),
        }
