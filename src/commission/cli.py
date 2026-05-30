"""交互式命令行入口"""

from commission.calculator import (
    AgentShare,
    BuyerCommissionResult,
    SellerCommissionResult,
    calc_buyer_commission,
    calc_seller_commission,
)
from commission.config import (
    PAYMENT_OPTIONS,
    PAYMENT_RATES,
    RENTAL,
    RENTAL_ROLES,
    SALE,
    SALE_ROLES,
)

# ── 工具函数 ──────────────────────────────────────────────

BORDER = "─" * 48


def _choose(prompt: str, options: list[str]) -> int:
    """数字快捷选择，返回索引"""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input(f"{prompt}（1-{len(options)}）: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"  ⚠ 请输入 1-{len(options)} 之间的数字")


def _choose_yes_no(prompt: str) -> bool:
    """y/n 选择"""
    while True:
        raw = input(f"{prompt}（y/n）: ").strip().lower()
        if raw in ("y", "n"):
            return raw == "y"
        print("  ⚠ 请输入 y 或 n")


def _input_amount(label: str) -> float:
    """输入正数金额"""
    while True:
        raw = input(f"{label}: ").strip()
        try:
            val = float(raw)
            if val > 0:
                return val
            print("  ⚠ 金额必须大于0")
        except ValueError:
            print("  ⚠ 请输入有效数字")


def _input_name(label: str) -> str:
    """输入业务员姓名"""
    raw = input(f"{label}: ").strip()
    return raw


def _pick_payment(label: str) -> str:
    """选择支付方式，返回方式名称"""
    print(f"\n{label}支付方式：")
    idx = _choose("请选择", PAYMENT_OPTIONS)
    name = PAYMENT_OPTIONS[idx]
    rate = PAYMENT_RATES[name]
    print(f"  → {name}（费率 {rate * 100:.2f}%）")
    return name


def _pick_my_roles(role_names: list[str]) -> list[str]:
    """逐个选择角色是否属于本店业务员"""
    print(f"\n哪些角色属于本店业务员？（逐个确认）")
    my_roles: list[str] = []
    for role in role_names:
        if _choose_yes_no(f"  {role} 是否属于本店？"):
            my_roles.append(role)
    return my_roles


def _pick_agent_roles(my_roles: list[str], buyer_role: bool = False) -> dict[str, str] | None:
    """为每个角色指定业务员姓名，返回角色→姓名映射"""
    if not my_roles:
        return None

    print("\n是否需要按业务员拆分佣金？")
    if not _choose_yes_no("  拆分"):
        return None

    agent_roles: dict[str, str] = {}
    all_same = _choose_yes_no("  所有角色属于同一业务员？")

    if all_same:
        name = _input_name("  业务员姓名")
        for role in my_roles:
            agent_roles[role] = name
        if buyer_role:
            agent_roles["客源成交人"] = name
    else:
        for role in my_roles:
            name = _input_name(f"  {role} 的业务员姓名")
            agent_roles[role] = name
        if buyer_role:
            buyer_name = _input_name("  客源成交人的业务员姓名")
            agent_roles["客源成交人"] = buyer_name

    return agent_roles


def _fmt_money(v: float) -> str:
    """格式化金额"""
    return f"{v:,.2f}"


def _show_agent_shares(shares: list[AgentShare]) -> None:
    """展示各业务员拆分明细"""
    if not shares or (len(shares) == 1 and shares[0].name == ""):
        return
    print(f"\n  ┌─ 业务员佣金拆分 ─────────────────────────")
    for s in shares:
        role_str = " + ".join(s.roles)
        pct = s.role_rate * 100
        if pct == int(pct):
            pct = int(pct)
        print(f"  │ {s.name}（{role_str} = {pct}%）")
        print(f"  │   份额 {_fmt_money(s.my_share)} - 德佑 {_fmt_money(s.beike_fee)} = 进店 {_fmt_money(s.store_income)}")
        print(f"  │   应发佣金: {_fmt_money(s.commission)} 元")
    print(f"  └──────────────────────────────────────────")


# ── 展示结果 ──────────────────────────────────────────────

def _show_buyer_result(r: BuyerCommissionResult) -> None:
    type_label = "租赁" if r.property_type == RENTAL else "买卖"
    print(f"\n{BORDER}")
    print(f"  【{type_label}·成交人视角】佣金计算明细")
    print(BORDER)

    # Step 1
    print(f"\n  Step 1  理房通平台费")
    print(f"    业主  {_fmt_money(r.owner_amount)} × {PAYMENT_RATES[r.owner_payment_method] * 100:.2f}% = {_fmt_money(r.owner_payment_fee)}")
    print(f"    客户  {_fmt_money(r.customer_amount)} × {PAYMENT_RATES[r.customer_payment_method] * 100:.2f}% = {_fmt_money(r.customer_payment_fee)}")
    print(f"    合计  {_fmt_money(r.total_payment_fee)}")

    # Step 2
    print(f"\n  Step 2  角色业绩拆分")
    for side, detail in [("业主", r.owner_detail), ("客户", r.customer_detail)]:
        print(f"    {side}方：")
        for role, share in detail.role_shares.items():
            owner_mark = "（本店）" if role in r.my_roles else "（它店）"
            print(f"      {role}  {_fmt_money(share)}{owner_mark}")

    # Step 3
    print(f"\n  Step 3  成交人实收佣金")
    for side, detail, received in [
        ("业主", r.owner_detail, r.owner_received),
        ("客户", r.customer_detail, r.customer_received),
    ]:
        other = sum(v for k, v in detail.role_shares.items() if k not in r.my_roles)
        print(f"    {side}方: {_fmt_money(detail.amount)} - {_fmt_money(detail.payment_fee)} - {_fmt_money(other)} = {_fmt_money(received)}")
    print(f"    合计  {_fmt_money(r.total_received)}")

    # Step 4
    print(f"\n  Step 4  德佑平台服务费")
    print(f"    {_fmt_money(r.total_received)} × 8% = {_fmt_money(r.beike_fee)}")

    # Step 5
    print(f"\n  Step 5  进店实收业绩")
    print(f"    {_fmt_money(r.total_received)} - {_fmt_money(r.beike_fee)} = {_fmt_money(r.store_income)}")

    # Step 6
    print(f"\n  Step 6  业务员应发佣金")
    print(f"    {_fmt_money(r.store_income)} × 50% = {_fmt_money(r.agent_commission)}")

    # 多业务员拆分
    _show_agent_shares(r.agent_shares)

    print(f"\n{BORDER}")
    if r.agent_shares and r.agent_shares[0].name != "":
        print(f"  ★ 各业务员到手见上方拆分明细")
    else:
        print(f"  ★ 业务员到手: {_fmt_money(r.agent_commission)} 元")
    print(BORDER)


def _show_seller_result(r: SellerCommissionResult) -> None:
    type_label = "租赁" if r.property_type == RENTAL else "买卖"
    print(f"\n{BORDER}")
    print(f"  【{type_label}·房源方视角】佣金计算明细")
    print(BORDER)

    roles = RENTAL_ROLES if r.property_type == RENTAL else SALE_ROLES
    my_rate = sum(rate for role, rate in roles.items() if role in r.my_roles)

    print(f"\n  我方角色: {' + '.join(r.my_roles)} = {my_rate * 100:.0f}%")
    print(f"  我方份额: {_fmt_money(r.total_amount)} × {my_rate * 100:.0f}% = {_fmt_money(r.my_share)}")

    print(f"\n  德佑平台服务费: {_fmt_money(r.my_share)} × 8% = {_fmt_money(r.beike_fee)}")
    print(f"  进店实收业绩: {_fmt_money(r.my_share)} - {_fmt_money(r.beike_fee)} = {_fmt_money(r.store_income)}")
    print(f"  业务员应发佣金: {_fmt_money(r.store_income)} × 50% = {_fmt_money(r.agent_commission)}")

    # 多业务员拆分
    _show_agent_shares(r.agent_shares)

    print(f"\n{BORDER}")
    if r.agent_shares and r.agent_shares[0].name != "":
        print(f"  ★ 各业务员到手见上方拆分明细")
    else:
        print(f"  ★ 业务员到手: {_fmt_money(r.agent_commission)} 元")
    print(BORDER)


# ── 主流程 ────────────────────────────────────────────────

def main() -> None:
    print("\n=== 佣金计算器 ===\n")

    # 1. 选择房源类型
    print("房源类型：")
    type_idx = _choose("请选择", ["租赁", "买卖"])
    property_type = RENTAL if type_idx == 0 else SALE
    role_names = list(RENTAL_ROLES.keys() if property_type == RENTAL else SALE_ROLES.keys())

    # 2. 选择视角
    print("\n计算视角：")
    view_idx = _choose("请选择", ["成交人（我店成交它店房源）", "房源方（它店成交我店房源）"])

    if view_idx == 0:
        # 成交人视角
        owner_amount = _input_amount("\n业主支付佣金")
        owner_method = _pick_payment("业主")
        customer_amount = _input_amount("\n客户支付佣金")
        customer_method = _pick_payment("客户")

        print("\n本店业务员兼任哪些房源方角色？")
        print("  快捷选择：")
        quick_idx = _choose("请选择", ["逐个选择", "全部属于本店", "全部不属于本店"])

        if quick_idx == 0:
            my_roles = _pick_my_roles(role_names)
        elif quick_idx == 1:
            my_roles = role_names[:]
        else:
            my_roles = []

        # 多业务员拆分
        all_roles_for_split = my_roles  # 不含客源成交人，由 _pick_agent_roles 自动处理
        agent_roles = _pick_agent_roles(all_roles_for_split, buyer_role=True)

        result = calc_buyer_commission(
            property_type=property_type,
            owner_amount=owner_amount,
            owner_payment_method=owner_method,
            customer_amount=customer_amount,
            customer_payment_method=customer_method,
            my_roles=my_roles,
            agent_roles=agent_roles,
        )
        _show_buyer_result(result)

    else:
        # 房源方视角
        total_amount = _input_amount("\n对方收佣金合计")

        print("\n本店业务员拥有哪些房源方角色？")
        print("  快捷选择：")
        quick_idx = _choose("请选择", ["逐个选择", "全部属于本店", "全部不属于本店"])

        if quick_idx == 0:
            my_roles = _pick_my_roles(role_names)
        elif quick_idx == 1:
            my_roles = role_names[:]
        else:
            my_roles = []

        # 多业务员拆分
        agent_roles = _pick_agent_roles(my_roles)

        result = calc_seller_commission(
            property_type=property_type,
            total_amount=total_amount,
            my_roles=my_roles,
            agent_roles=agent_roles,
        )
        _show_seller_result(result)

    print()


if __name__ == "__main__":
    main()
