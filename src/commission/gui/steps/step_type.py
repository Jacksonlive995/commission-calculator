"""Step 1: 房源类型 + 计算视角"""

from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from commission.config import RENTAL, SALE


class StepType(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        # 房源类型
        layout.addWidget(QLabel("房源类型"))
        self.bg_type = QButtonGroup(self)
        self.rb_rental = QRadioButton("租赁")
        self.rb_sale = QRadioButton("买卖")
        self.rb_rental.setChecked(True)
        self.bg_type.addButton(self.rb_rental, 0)
        self.bg_type.addButton(self.rb_sale, 1)
        layout.addWidget(self.rb_rental)
        layout.addWidget(self.rb_sale)

        layout.addSpacing(16)

        # 计算视角
        layout.addWidget(QLabel("计算视角"))
        self.bg_view = QButtonGroup(self)
        self.rb_buyer = QRadioButton("成交人（我店成交它店房源）")
        self.rb_seller = QRadioButton("房源方（它店成交我店房源）")
        self.rb_buyer.setChecked(True)
        self.bg_view.addButton(self.rb_buyer, 0)
        self.bg_view.addButton(self.rb_seller, 1)
        layout.addWidget(self.rb_buyer)
        layout.addWidget(self.rb_seller)

        layout.addStretch()

    def validate(self) -> bool:
        return True

    def get_state(self) -> dict:
        return {
            "property_type": RENTAL if self.rb_rental.isChecked() else SALE,
            "view": "buyer" if self.rb_buyer.isChecked() else "seller",
        }
