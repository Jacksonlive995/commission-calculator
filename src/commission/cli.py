"""交互式命令行入口"""

from commission.calculator import (
    calc_buyer_commission,
    calc_seller_commission,
)
from commission.config import (
    PAYMENT_OPTIONS,
    PAYMENT_RATES,
    PLATFORM_ROLES,
    RENTAL,
    RENTAL_ROLES,
    SALE,
    SALE_ROLES,
)
from commission.formatter import format_buyer_result, format_seller_result


# ── 工具函数 ──────────────────────────────────────────────


def _choose(prompt: str, options: list[str]) -> int:
    """数字快捷选择，返回索引"""
    for i, opt in enumerate(options, 1):
        print(f" {i}. {opt}")
    while True:
        raw = input(f"{prompt}（1-{len(options)}）: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f" ⚠ 请输入 1-{len(options)} 之间的数字")


def _choose_yes_no(prompt: str) -> bool:
    """y/n 选择"""
    while True:
        raw = input(f"{prompt}（y/n）: ").strip().lower()
        if raw in ("y", "n"):
            return raw == "y"
        print(" ⚠ 请输入 y 或 n")


def _ask_write_feishu(result, view: str, property_type: str, total_amount: float = 0.0) -> None:
    """询问是否写入飞书多维表格"""
    print()
    print("是否将结果写入飞书多维表格？")
    if not _choose_yes_no(" 写入飞书"):
        return
    try:
        from commission.feishu import write_to_feishu
        from commission.records import extract_records
        records = extract_records(result, view, property_type, total_amount)
        if not records:
            print(" ⚠ 没有可写入的记录")
            return
        url = write_to_feishu(records)
        print(f" ✓ 已写入飞书多维表格: {url}")
    except Exception as e:
        print(f" ✗ 写入飞书失败: {e}")


def _input_amount(label: str) -> float:
    """输入正数金额"""
    while True:
        raw = input(f"{label}: ").strip()
        try:
            val = float(raw)
            if val > 0:
                return val
            print(" ⚠ 金额必须大于0")
        except ValueError:
            print(" ⚠ 请输入有效数字")


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
    print(f" → {name}（费率 {rate * 100:.2f}%）")
    return name


def _pick_my_roles(role_names: list[str]) -> list[str]:
    """逐个选择角色是否属于本店业务员"""
    print(f"\n哪些角色属于本店业务员？（逐个确认）")
    my_roles: list[str] = []
    for role in role_names:
        if _choose_yes_no(f" {role} 是否属于本店？"):
            my_roles.append(role)
    return my_roles


def _pick_agent_roles(my_roles: list[str], buyer_role: bool = False) -> dict[str, str] | None:
    """为每个角色指定业务员姓名，返回角色→姓名映射"""
    if not my_roles:
        return None

    print("\n是否需要按业务员拆分佣金？")
    if not _choose_yes_no(" 拆分"):
        return None

    agent_roles: dict[str, str] = {}
    all_same = _choose_yes_no(" 所有角色属于同一业务员？")

    if all_same:
        name = _input_name(" 业务员姓名")
        for role in my_roles:
            agent_roles[role] = name
        if buyer_role:
            agent_roles["客源成交人"] = name
    else:
        for role in my_roles:
            name = _input_name(f" {role} 的业务员姓名")
            agent_roles[role] = name
        if buyer_role:
            buyer_name = _input_name(" 客源成交人的业务员姓名")
            agent_roles["客源成交人"] = buyer_name

    return agent_roles


# ── 主流程 ────────────────────────────────────────────────


def main() -> None:
    print("\n=== 佣金计算器 ===\n")

    # 1. 选择房源类型
    print("房源类型：")
    type_idx = _choose("请选择", ["租赁", "买卖"])
    property_type = RENTAL if type_idx == 0 else SALE
    all_roles = RENTAL_ROLES if property_type == RENTAL else SALE_ROLES
    role_names = [r for r in all_roles if r not in PLATFORM_ROLES]

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
        print(" 快捷选择：")
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
        print()
        print(format_buyer_result(result))
        _ask_write_feishu(result, "buyer", property_type, owner_amount + customer_amount)

    else:
        # 房源方视角
        total_amount = _input_amount("\n对方收佣金合计")

        print("\n本店业务员拥有哪些房源方角色？")
        print(" 快捷选择：")
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
        print()
        print(format_seller_result(result))
        _ask_write_feishu(result, "seller", property_type, total_amount)

    print()


if __name__ == "__main__":
    main()
