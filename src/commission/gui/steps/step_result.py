"""Step 5: 结果展示"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from commission.calculator import BuyerCommissionResult, SellerCommissionResult
from commission.config import PAYMENT_RATES, RENTAL, RENTAL_ROLES, SALE_ROLES


class StepResult(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setStyleSheet("font-family: 'Consolas', 'Microsoft YaHei', monospace; font-size: 13px;")
        layout.addWidget(self.text_result, 1)

        self.btn_copy = QPushButton("复制结果")
        self.btn_copy.setFixedWidth(120)
        layout.addWidget(self.btn_copy, 0, Qt.AlignmentFlag.AlignRight)
        self.btn_copy.clicked.connect(self._copy)

    def validate(self) -> bool:
        return True

    def show_result(self, result: BuyerCommissionResult | SellerCommissionResult) -> None:
        if isinstance(result, BuyerCommissionResult):
            self.text_result.setPlainText(self._format_buyer(result))
        else:
            self.text_result.setPlainText(self._format_seller(result))

    def _copy(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_result.toPlainText())

    # ── 格式化 ───────────────────────────────────────────

    @staticmethod
    def _fmt(v: float) -> str:
        return f"{v:,.2f}"

    @staticmethod
    def _border() -> str:
        return "─" * 48

    def _format_buyer(self, r: BuyerCommissionResult) -> str:
        b = self._border()
        f = self._fmt
        type_label = "租赁" if r.property_type == RENTAL else "买卖"
        lines = [
            b,
            f" 【{type_label}·成交人视角】佣金计算明细",
            b,
            "",
            " Step 1 理房通平台费",
            f"  业主 {f(r.owner_amount)} × {PAYMENT_RATES[r.owner_payment_method] * 100:.2f}% = {f(r.owner_payment_fee)}",
            f"  客户 {f(r.customer_amount)} × {PAYMENT_RATES[r.customer_payment_method] * 100:.2f}% = {f(r.customer_payment_fee)}",
            f"  合计 {f(r.total_payment_fee)}",
            "",
            " Step 2 角色业绩拆分",
        ]
        for side, detail in [("业主", r.owner_detail), ("客户", r.customer_detail)]:
            lines.append(f"  {side}方：")
            for role, share in detail.role_shares.items():
                mark = "（本店）" if role in r.my_roles else "（它店）"
                lines.append(f"   {role} {f(share)}{mark}")
            if detail.platform_viewing_fee > 0:
                lines.append(f"   平台实勘 {f(detail.platform_viewing_fee)}（平台收取）")

        lines += [
            "",
            " Step 3 成交人实收佣金",
        ]
        for side, detail, received in [
            ("业主", r.owner_detail, r.owner_received),
            ("客户", r.customer_detail, r.customer_received),
        ]:
            other = sum(v for k, v in detail.role_shares.items() if k not in r.my_roles)
            lines.append(f"  {side}方: {f(detail.amount)} - {f(detail.payment_fee)} - {f(other)} = {f(received)}")
        lines.append(f"  合计 {f(r.total_received)}")

        lines += [
            "",
            " Step 4 德佑平台服务费",
            f"  {f(r.total_received)} × 8% = {f(r.beike_fee)}",
            "",
            " Step 5 进店实收业绩",
            f"  {f(r.total_received)} - {f(r.beike_fee)} = {f(r.store_income)}",
            "",
            " Step 6 业务员应发佣金",
            f"  {f(r.store_income)} × 50% = {f(r.agent_commission)}",
        ]

        lines += self._format_agent_shares(r.agent_shares)
        lines.append("")
        if r.agent_shares and r.agent_shares[0].name != "":
            lines.append(f" ★ 各业务员到手见上方拆分明细")
        else:
            lines.append(f" ★ 业务员到手: {f(r.agent_commission)} 元")
        lines.append(b)
        return "\n".join(lines)

    def _format_seller(self, r: SellerCommissionResult) -> str:
        b = self._border()
        f = self._fmt
        type_label = "租赁" if r.property_type == RENTAL else "买卖"
        roles = RENTAL_ROLES if r.property_type == RENTAL else SALE_ROLES
        my_rate = sum(rate for role, rate in roles.items() if role in r.my_roles)

        lines = [
            b,
            f" 【{type_label}·房源方视角】佣金计算明细",
            b,
            "",
            f" 我方角色: {' + '.join(r.my_roles)} = {my_rate * 100:.0f}%",
            f" 我方份额: {f(r.total_amount)} × {my_rate * 100:.0f}% = {f(r.my_share)}",
            "",
            f" 德佑平台服务费: {f(r.my_share)} × 8% = {f(r.beike_fee)}",
            f" 进店实收业绩: {f(r.my_share)} - {f(r.beike_fee)} = {f(r.store_income)}",
            f" 业务员应发佣金: {f(r.store_income)} × 50% = {f(r.agent_commission)}",
        ]
        lines += self._format_agent_shares(r.agent_shares)
        lines.append("")
        if r.agent_shares and r.agent_shares[0].name != "":
            lines.append(f" ★ 各业务员到手见上方拆分明细")
        else:
            lines.append(f" ★ 业务员到手: {f(r.agent_commission)} 元")
        lines.append(b)
        return "\n".join(lines)

    def _format_agent_shares(self, shares: list) -> list[str]:
        if not shares or (len(shares) == 1 and shares[0].name == ""):
            return []
        f = self._fmt
        lines = ["", " ┌─ 业务员佣金拆分 ─────────────────────────"]
        for s in shares:
            role_str = " + ".join(s.roles)
            pct = s.role_rate * 100
            if pct == int(pct):
                pct = int(pct)
            lines.append(f" │ {s.name}（{role_str} = {pct}%）")
            lines.append(f" │  份额 {f(s.my_share)} - 德佑 {f(s.beike_fee)} = 进店 {f(s.store_income)}")
            lines.append(f" │  应发佣金: {f(s.commission)} 元")
            lines.append(f" └──────────────────────────────────────────")
        return lines
