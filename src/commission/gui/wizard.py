"""佣金计算向导主窗口"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from commission.gui.steps.step_payment import StepPayment
from commission.gui.steps.step_result import StepResult
from commission.gui.steps.step_roles import StepRoles
from commission.gui.steps.step_split import StepSplit
from commission.gui.steps.step_type import StepType

STEP_LABELS = ["① 房源类型", "② 支付信息", "③ 角色归属", "④ 拆分设置", "⑤ 结果"]


class CommissionWizard(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("佣金计算器")
        self.setMinimumSize(680, 520)
        self._init_ui()

    # ── UI 搭建 ──────────────────────────────────────────

    def _init_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 16)

        # 步骤指示器
        self.step_indicator = QLabel()
        self.step_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_indicator.setStyleSheet("font-size:15px; font-weight:bold; color:#444;")
        layout.addWidget(self.step_indicator)

        # 页面容器
        self.stack = QStackedWidget()
        self.step_type = StepType()
        self.step_payment = StepPayment()
        self.step_roles = StepRoles()
        self.step_split = StepSplit()
        self.step_result = StepResult()
        self.stack.addWidget(self.step_type)
        self.stack.addWidget(self.step_payment)
        self.stack.addWidget(self.step_roles)
        self.stack.addWidget(self.step_split)
        self.stack.addWidget(self.step_result)
        layout.addWidget(self.stack, 1)

        # 导航按钮
        btn_row = QHBoxLayout()
        self.btn_prev = QPushButton("上一步")
        self.btn_next = QPushButton("下一步")
        self.btn_prev.setFixedWidth(100)
        self.btn_next.setFixedWidth(100)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_prev)
        btn_row.addWidget(self.btn_next)
        layout.addLayout(btn_row)

        self.btn_prev.clicked.connect(self._go_prev)
        self.btn_next.clicked.connect(self._go_next)

        self._current_step = 0
        self._update_nav()

    # ── 步骤导航 ─────────────────────────────────────────

    @property
    def current_step(self) -> int:
        return self._current_step

    @current_step.setter
    def current_step(self, idx: int) -> None:
        self._current_step = idx
        self.stack.setCurrentIndex(idx)
        self._update_nav()
        # 进入步骤时初始化
        if idx == 1:
            self.step_payment.setup(self.step_type.get_state())
        elif idx == 2:
            self.step_roles.setup(self.step_type.get_state())
        elif idx == 3:
            self.step_split.setup(self.step_type.get_state(), self.step_roles.get_state())
        elif idx == 4:
            self._run_calculation()

    def _update_nav(self) -> None:
        idx = self._current_step
        total = self.stack.count()
        self.step_indicator.setText("  →  ".join(
            f"【{l}】" if i == idx else l for i, l in enumerate(STEP_LABELS)
        ))
        self.btn_prev.setEnabled(idx > 0)
        if idx == 0:
            self.btn_next.setText("下一步")
        elif idx < total - 1:
            self.btn_next.setText("下一步")
        else:
            self.btn_next.setText("重新计算")

    def _go_prev(self) -> None:
        if self._current_step > 0:
            self.current_step -= 1

    def _go_next(self) -> None:
        idx = self._current_step
        pages = [self.step_type, self.step_payment, self.step_roles, self.step_split, self.step_result]
        page = pages[idx]
        if not page.validate():
            return
        if idx == self.stack.count() - 1:
            # 重新计算 → 回到第0步
            self.current_step = 0
        else:
            self.current_step = idx + 1

    # ── 计算与展示 ───────────────────────────────────────

    def _run_calculation(self) -> None:
        from commission.calculator import calc_buyer_commission, calc_seller_commission

        ts = self.step_type.get_state()
        ps = self.step_payment.get_state()
        rs = self.step_roles.get_state()
        ss = self.step_split.get_state()

        if ts["view"] == "buyer":
            result = calc_buyer_commission(
                property_type=ts["property_type"],
                owner_amount=ps["owner_amount"],
                owner_payment_method=ps["owner_method"],
                customer_amount=ps["customer_amount"],
                customer_payment_method=ps["customer_method"],
                my_roles=rs["my_roles"],
                agent_roles=ss.get("agent_roles"),
            )
            self.step_result.show_result(
                result,
                view="buyer",
                property_type=ts["property_type"],
                total_amount=ps["owner_amount"] + ps["customer_amount"],
            )
        else:
            result = calc_seller_commission(
                property_type=ts["property_type"],
                total_amount=ps["total_amount"],
                my_roles=rs["my_roles"],
                agent_roles=ss.get("agent_roles"),
            )
            self.step_result.show_result(
                result,
                view="seller",
                property_type=ts["property_type"],
                total_amount=ps["total_amount"],
            )
