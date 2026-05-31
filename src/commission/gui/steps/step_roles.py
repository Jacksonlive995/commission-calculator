"""Step 3: 角色归属"""

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from commission.config import PLATFORM_ROLES, RENTAL, RENTAL_ROLES, SALE_ROLES


class StepRoles(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._role_names: list[str] = []
        self._checkboxes: list[QCheckBox] = []
        self._init_ui()

    def _init_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(10)

        title = QLabel("选择本店持有的角色")
        title.setObjectName("PageTitle")
        self._layout.addWidget(title)

        subtitle = QLabel("平台角色不会出现在可选列表中。")
        subtitle.setObjectName("PageSubtitle")
        self._layout.addWidget(subtitle)

        self.lbl_hint = QLabel()
        self.lbl_hint.setWordWrap(True)
        self._layout.addWidget(self.lbl_hint)

        # 快捷按钮行
        btn_row_widget = QWidget()
        self._btn_row = QHBoxLayout(btn_row_widget)
        self._btn_row.setContentsMargins(0, 4, 0, 4)
        self.btn_all = QPushButton("全部属于本店")
        self.btn_none = QPushButton("全部不属于本店")
        self._btn_row.addWidget(self.btn_all)
        self._btn_row.addWidget(self.btn_none)
        self._layout.addWidget(btn_row_widget)

        self.btn_all.clicked.connect(self._select_all)
        self.btn_none.clicked.connect(self._select_none)

        # 角色复选框容器
        self._cb_widget = QWidget()
        self._cb_layout = QVBoxLayout(self._cb_widget)
        self._cb_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._cb_widget)

        self._layout.addStretch()

    def setup(self, type_state: dict) -> None:
        property_type = type_state["property_type"]
        is_buyer = type_state["view"] == "buyer"
        roles = RENTAL_ROLES if property_type == RENTAL else SALE_ROLES
        self._role_names = [r for r in roles if r not in PLATFORM_ROLES]

        # 清除旧复选框
        while self._cb_layout.count():
            item = self._cb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if is_buyer:
            self.lbl_hint.setText("本店业务员兼任哪些房源方角色？")
        else:
            self.lbl_hint.setText("本店业务员拥有哪些房源方角色？")

        self._checkboxes: list[QCheckBox] = []
        for role in self._role_names:
            pct = int(roles[role] * 100)
            cb = QCheckBox(f"{role}（{pct}%）")
            self._cb_layout.addWidget(cb)
            self._checkboxes.append(cb)

    def _select_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(True)

    def _select_none(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(False)

    def validate(self) -> bool:
        return True  # 可以全部不属于本店

    def get_state(self) -> dict:
        my_roles = [
            name for name, cb in zip(self._role_names, self._checkboxes)
            if cb.isChecked()
        ]
        return {"my_roles": my_roles}
