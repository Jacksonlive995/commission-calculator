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
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        title = QLabel("选择房源类型和计算视角")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        subtitle = QLabel("先确认业务场景，再进入金额和角色配置。")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        # 房源类型
        label_type = QLabel("房源类型")
        label_type.setObjectName("SectionTitle")
        layout.addWidget(label_type)
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
        label_view = QLabel("计算视角")
        label_view.setObjectName("SectionTitle")
        layout.addWidget(label_view)
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
