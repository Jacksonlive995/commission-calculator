"""佣金计算结果文本格式化。"""

from commission.calculator import AgentShare, BuyerCommissionResult, SellerCommissionResult
from commission.config import PAYMENT_RATES, PLATFORM_ROLES, RENTAL, RENTAL_ROLES, SALE_ROLES


def format_money(value: float) -> str:
    return f"{value:,.2f}"


def border() -> str:
    return "─" * 48


def format_agent_shares(shares: list[AgentShare]) -> list[str]:
    if not shares or (len(shares) == 1 and shares[0].name == ""):
        return []

    lines = ["", " ┌─ 业务员佣金拆分 ─────────────────────────"]
    for share in shares:
        role_str = " + ".join(share.roles)
        pct = share.role_rate * 100
        if pct == int(pct):
            pct = int(pct)
        lines.append(f" │ {share.name}（{role_str} = {pct}%）")
        lines.append(
            f" │  份额 {format_money(share.my_share)} - 德佑 {format_money(share.beike_fee)} = 进店 {format_money(share.store_income)}"
        )
        lines.append(f" │  应发佣金: {format_money(share.commission)} 元")
    lines.append(" └──────────────────────────────────────────")
    return lines


def format_buyer_result(result: BuyerCommissionResult) -> str:
    type_label = "租赁" if result.property_type == RENTAL else "买卖"
    lines = [
        border(),
        f" 【{type_label}·成交人视角】佣金计算明细",
        border(),
        "",
        " Step 1 理房通平台费",
        f"  业主 {format_money(result.owner_amount)} × {PAYMENT_RATES[result.owner_payment_method] * 100:.2f}% = {format_money(result.owner_payment_fee)}",
        f"  客户 {format_money(result.customer_amount)} × {PAYMENT_RATES[result.customer_payment_method] * 100:.2f}% = {format_money(result.customer_payment_fee)}",
        f"  合计 {format_money(result.total_payment_fee)}",
        "",
        " Step 2 角色业绩拆分",
    ]

    for side, detail in [("业主", result.owner_detail), ("客户", result.customer_detail)]:
        lines.append(f"  {side}方：")
        for role, share in detail.role_shares.items():
            if role in PLATFORM_ROLES:
                mark = "（平台收取）"
            elif role in result.my_roles:
                mark = "（本店）"
            else:
                mark = "（它店）"
            lines.append(f"   {role} {format_money(share)}{mark}")

    lines += ["", " Step 3 成交人实收佣金"]
    for side, detail, received in [
        ("业主", result.owner_detail, result.owner_received),
        ("客户", result.customer_detail, result.customer_received),
    ]:
        other = sum(value for role, value in detail.role_shares.items() if role not in result.my_roles)
        lines.append(
            f"  {side}方: {format_money(detail.amount)} - {format_money(detail.payment_fee)} - {format_money(other)} = {format_money(received)}"
        )
    lines.append(f"  合计 {format_money(result.total_received)}")

    lines += [
        "",
        " Step 4 德佑平台服务费",
        f"  {format_money(result.total_received)} × 8% = {format_money(result.beike_fee)}",
        "",
        " Step 5 进店实收业绩",
        f"  {format_money(result.total_received)} - {format_money(result.beike_fee)} = {format_money(result.store_income)}",
        "",
        " Step 6 业务员应发佣金",
        f"  {format_money(result.store_income)} × 50% = {format_money(result.agent_commission)}",
    ]

    lines += format_agent_shares(result.agent_shares)
    lines.append("")
    if result.agent_shares and result.agent_shares[0].name != "":
        lines.append(" ★ 各业务员到手见上方拆分明细")
    else:
        lines.append(f" ★ 业务员到手: {format_money(result.agent_commission)} 元")
    lines.append(border())
    return "\n".join(lines)


def format_seller_result(result: SellerCommissionResult) -> str:
    type_label = "租赁" if result.property_type == RENTAL else "买卖"
    roles = RENTAL_ROLES if result.property_type == RENTAL else SALE_ROLES
    my_rate = sum(rate for role, rate in roles.items() if role in result.my_roles)

    lines = [
        border(),
        f" 【{type_label}·房源方视角】佣金计算明细",
        border(),
        "",
        f" 我方角色: {' + '.join(result.my_roles)} = {my_rate * 100:.0f}%",
        f" 我方份额: {format_money(result.total_amount)} × {my_rate * 100:.0f}% = {format_money(result.my_share)}",
        "",
        f" 德佑平台服务费: {format_money(result.my_share)} × 8% = {format_money(result.beike_fee)}",
        f" 进店实收业绩: {format_money(result.my_share)} - {format_money(result.beike_fee)} = {format_money(result.store_income)}",
        f" 业务员应发佣金: {format_money(result.store_income)} × 50% = {format_money(result.agent_commission)}",
    ]
    lines += format_agent_shares(result.agent_shares)
    lines.append("")
    if result.agent_shares and result.agent_shares[0].name != "":
        lines.append(" ★ 各业务员到手见上方拆分明细")
    else:
        lines.append(f" ★ 业务员到手: {format_money(result.agent_commission)} 元")
    lines.append(border())
    return "\n".join(lines)
