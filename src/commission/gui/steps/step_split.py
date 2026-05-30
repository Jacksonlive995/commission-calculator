"""Step 4: 拆分设置"""

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QRadioButton,
    QButtonGroup,
    QVBoxLayout,
    QWidget,
)



class StepSplit(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._is_buyer = True
        self._my_roles: list[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        self._layout = QVBoxLayout(self)

        self.cb_split = QCheckBox("按业务员拆分佣金")
        self._layout.addWidget(self.cb_split)
        self.cb_split.toggled.connect(self._on_split_toggled)

        # 拆分选项容器
        self._split_widget = QWidget()
        self._split_layout = QVBoxLayout(self._split_widget)
        self._split_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._split_widget)

        # 同一人 / 逐个指定
        self.bg_same = QButtonGroup(self)
        self.rb_same = QRadioButton("所有角色属于同一业务员")
        self.rb_each = QRadioButton("逐个指定业务员")
        self.rb_same.setChecked(True)
        self.bg_same.addButton(self.rb_same, 0)
        self.bg_same.addButton(self.rb_each, 1)
        self._split_layout.addWidget(self.rb_same)
        self._split_layout.addWidget(self.rb_each)
        self.bg_same.idToggled.connect(self._on_same_toggled)

        # 同一人姓名
        self._same_widget = QWidget()
        same_layout = QFormLayout(self._same_widget)
        self.le_same_name = QLineEdit()
        self.le_same_name.setPlaceholderText("输入业务员姓名")
        same_layout.addRow("业务员姓名：", self.le_same_name)
        self._split_layout.addWidget(self._same_widget)

        # 逐个指定容器
        self._each_widget = QWidget()
        self._each_layout = QFormLayout(self._each_widget)
        self._each_layout.setContentsMargins(0, 0, 0, 0)
        self._split_layout.addWidget(self._each_widget)

        self._layout.addStretch()

        self._split_widget.setVisible(False)

    def setup(self, type_state: dict, roles_state: dict) -> None:
        self._is_buyer = type_state["view"] == "buyer"
        self._my_roles = roles_state["my_roles"]
        self._rebuild_each_fields()
        if not self._my_roles:
            self.cb_split.setChecked(False)
            self.cb_split.setEnabled(False)
        else:
            self.cb_split.setEnabled(True)

    def _rebuild_each_fields(self) -> None:
        # 清除旧字段
        while self._each_layout.count():
            item = self._each_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._each_inputs: dict[str, QLineEdit] = {}
        for role in self._my_roles:
            le = QLineEdit()
            le.setPlaceholderText(f"{role} 的业务员姓名")
            self._each_layout.addRow(f"{role}：", le)
            self._each_inputs[role] = le

        if self._is_buyer:
            le = QLineEdit()
            le.setPlaceholderText("客源成交人的业务员姓名")
            self._each_layout.addRow("客源成交人：", le)
            self._each_inputs["客源成交人"] = le

    def _on_split_toggled(self, checked: bool) -> None:
        self._split_widget.setVisible(checked)

    def _on_same_toggled(self, idx: int, checked: bool) -> None:
        if idx == 0 and checked:
            self._same_widget.setVisible(True)
            self._each_widget.setVisible(False)
        elif idx == 1 and checked:
            self._same_widget.setVisible(False)
            self._each_widget.setVisible(True)

    def validate(self) -> bool:
        if not self.cb_split.isChecked():
            return True
        if not self._my_roles:
            return True
        if self.rb_same.isChecked():
            return bool(self.le_same_name.text().strip())
        # 逐个指定：每个角色都必须有姓名
        return all(le.text().strip() for le in self._each_inputs.values())

    def get_state(self) -> dict:
        if not self.cb_split.isChecked() or not self._my_roles:
            return {}

        agent_roles: dict[str, str] = {}
        if self.rb_same.isChecked():
            name = self.le_same_name.text().strip()
            for role in self._my_roles:
                agent_roles[role] = name
            if self._is_buyer:
                agent_roles["客源成交人"] = name
        else:
            for role, le in self._each_inputs.items():
                agent_roles[role] = le.text().strip()

        return {"agent_roles": agent_roles}
