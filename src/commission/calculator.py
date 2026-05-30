"""佣金计算核心逻辑

所有函数都是纯函数，不涉及IO操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from commission.config import (
    AGENT_COMMISSION_RATE,
    BEIKE_PLATFORM_RATE,
    PAYMENT_RATES,
    RENTAL,
    RENTAL_ROLES,
    SALE,
    SALE_PLATFORM_VIEWING_RATE,
    SALE_ROLES,
)


@dataclass
class AgentShare:
    """单个业务员的佣金拆分明细"""

    name: str = ""
    roles: list[str] = field(default_factory=list)
    role_rate: float = 0.0
    my_share: float = 0.0
    beike_fee: float = 0.0
    store_income: float = 0.0
    commission: float = 0.0


@dataclass
class PaymentDetail:
    """单笔支付的分账明细"""

    amount: float = 0.0
    payment_method: str = ""
    payment_fee: float = 0.0
    role_shares: dict[str, float] = field(default_factory=dict)
    platform_viewing_fee: float = 0.0
    buyer_share: float = 0.0


@dataclass
class BuyerCommissionResult:
    """成交人视角的计算结果"""

    # 输入
    property_type: str
    owner_amount: float
    owner_payment_method: str
    customer_amount: float
    customer_payment_method: str
    my_roles: list[str]

    # Step 1: 理房通平台费
    owner_payment_fee: float = 0.0
    customer_payment_fee: float = 0.0
    total_payment_fee: float = 0.0

    # Step 2: 角色业绩拆分
    owner_detail: PaymentDetail = field(default_factory=PaymentDetail)
    customer_detail: PaymentDetail = field(default_factory=PaymentDetail)

    # Step 3: 成交人实收佣金
    owner_received: float = 0.0
    customer_received: float = 0.0
    total_received: float = 0.0

    # Step 4: 德佑平台服务费
    beike_fee: float = 0.0

    # Step 5: 进店实收业绩
    store_income: float = 0.0

    # Step 6: 业务员应发佣金
    agent_commission: float = 0.0
    agent_shares: list[AgentShare] = field(default_factory=list)


@dataclass
class SellerCommissionResult:
    """房源方视角的计算结果"""

    property_type: str
    total_amount: float
    my_roles: list[str]

    my_share: float = 0.0
    beike_fee: float = 0.0
    store_income: float = 0.0
    agent_commission: float = 0.0
    agent_shares: list[AgentShare] = field(default_factory=list)


def calc_payment_fee(amount: float, payment_method: str) -> float:
    """计算理房通平台费"""
    rate = PAYMENT_RATES[payment_method]
    return round(amount * rate, 2)


def _get_roles(property_type: str) -> dict[str, float]:
    """获取房源类型的角色配置"""
    return RENTAL_ROLES if property_type == RENTAL else SALE_ROLES


def _calc_buyer_role_rate(property_type: str, my_roles: list[str]) -> float:
    """计算成交人实际占比（100% - 其他门店角色占比）"""
    roles = _get_roles(property_type)
    other_store_rate = sum(rate for role, rate in roles.items() if role not in my_roles)
    return 1.0 - other_store_rate


def calc_agent_shares(
    total_share: float,
    property_type: str,
    my_roles: list[str],
    agent_roles: dict[str, str] | None = None,
    buyer_rate: float | None = None,
) -> list[AgentShare]:
    """按角色拆分各业务员应得佣金

    total_share: 未扣德佑费的我方总份额（成交人视角为 total_received，房源方视角为 my_share）
    property_type: 房源类型
    my_roles: 本方持有的角色列表（成交人视角不含"客源成交人"，该角色通过 buyer_rate 传入）
    agent_roles: 角色→业务员姓名映射。为空时生成一条总记录。
    buyer_rate: 成交人角色占比，仅成交人视角使用
    """
    roles = _get_roles(property_type)

    if not agent_roles:
        return [AgentShare(
            name="",
            roles=my_roles[:],
            role_rate=sum(rate for role, rate in roles.items() if role in my_roles),
            my_share=total_share,
            beike_fee=0.0,
            store_income=total_share,
            commission=round(total_share * AGENT_COMMISSION_RATE, 2),
        )]

    # 构建角色→占比映射（含客源成交人）
    role_rates: dict[str, float] = dict(roles)
    if buyer_rate is not None:
        role_rates["客源成交人"] = buyer_rate

    # 按业务员分组角色
    agent_map: dict[str, list[str]] = {}
    for role, name in agent_roles.items():
        if role in my_roles or (buyer_rate is not None and role == "客源成交人"):
            agent_map.setdefault(name, []).append(role)

    shares: list[AgentShare] = []
    for name, role_list in agent_map.items():
        rate = sum(role_rates[r] for r in role_list)
        my_share = round(total_share * rate, 2)
        beike = round(my_share * BEIKE_PLATFORM_RATE, 2)
        store = round(my_share - beike, 2)
        commission = round(store * AGENT_COMMISSION_RATE, 2)
        shares.append(AgentShare(
            name=name,
            roles=role_list,
            role_rate=rate,
            my_share=my_share,
            beike_fee=beike,
            store_income=store,
            commission=commission,
        ))
    return shares


def calc_buyer_commission(
    property_type: str,
    owner_amount: float,
    owner_payment_method: str,
    customer_amount: float,
    customer_payment_method: str,
    my_roles: list[str],
    agent_roles: dict[str, str] | None = None,
) -> BuyerCommissionResult:
    """计算成交人视角的完整佣金

    agent_roles: 角色→业务员姓名映射，用于拆分各业务员应发佣金。
                 例如 {"录入人": "张三", "维护人": "李四"}
                 成交人角色（客源成交人）会自动分配给名为"成交人"的业务员。
    """
    result = BuyerCommissionResult(
        property_type=property_type,
        owner_amount=owner_amount,
        owner_payment_method=owner_payment_method,
        customer_amount=customer_amount,
        customer_payment_method=customer_payment_method,
        my_roles=my_roles,
    )

    roles = _get_roles(property_type)
    buyer_rate = _calc_buyer_role_rate(property_type, my_roles)

    # Step 1: 理房通平台费
    result.owner_payment_fee = calc_payment_fee(owner_amount, owner_payment_method)
    result.customer_payment_fee = calc_payment_fee(customer_amount, customer_payment_method)
    result.total_payment_fee = round(result.owner_payment_fee + result.customer_payment_fee, 2)

    # Step 2 & 3: 对每笔支付分别计算
    for prefix, amount, payment_method in [
        ("owner", owner_amount, owner_payment_method),
        ("customer", customer_amount, customer_payment_method),
    ]:
        payment_fee = getattr(result, f"{prefix}_payment_fee")
        detail = PaymentDetail(amount=amount, payment_method=payment_method, payment_fee=payment_fee)

        # 各角色份额
        other_store_shares = 0.0
        for role, rate in roles.items():
            share = round(amount * rate, 2)
            detail.role_shares[role] = share
            if role not in my_roles:
                other_store_shares += share

        # 平台实勘费（仅买卖），由平台直接收取，不从成交人份额中扣除
        if property_type == SALE:
            detail.platform_viewing_fee = round(amount * SALE_PLATFORM_VIEWING_RATE, 2)

        # 成交人份额
        detail.buyer_share = round(amount - payment_fee - other_store_shares, 2)

        setattr(result, f"{prefix}_detail", detail)
        setattr(result, f"{prefix}_received", detail.buyer_share)

    result.total_received = round(result.owner_received + result.customer_received, 2)

    # Step 4: 德佑平台服务费
    result.beike_fee = round(result.total_received * BEIKE_PLATFORM_RATE, 2)

    # Step 5: 进店实收业绩
    result.store_income = round(result.total_received - result.beike_fee, 2)

    # Step 6: 业务员应发佣金
    result.agent_commission = round(result.store_income * AGENT_COMMISSION_RATE, 2)

    # 拆分各业务员应发佣金
    if agent_roles:
        # 成交人角色（客源成交人）自动分配给名为"成交人"的业务员
        full_agent_roles: dict[str, str] = dict(agent_roles)
        full_agent_roles.setdefault("客源成交人", "成交人")
        result.agent_shares = calc_agent_shares(
            result.total_received, property_type, my_roles, full_agent_roles,
            buyer_rate=buyer_rate,
        )
    else:
        result.agent_shares = calc_agent_shares(
            result.store_income, property_type, my_roles, None,
        )

    return result


def calc_seller_commission(
    property_type: str,
    total_amount: float,
    my_roles: list[str],
    agent_roles: dict[str, str] | None = None,
) -> SellerCommissionResult:
    """计算房源方视角的佣金（它店成交我店房源）

    agent_roles: 角色→业务员姓名映射，用于拆分各业务员应发佣金。
                 例如 {"录入人": "张三", "维护人": "李四"}
    """
    result = SellerCommissionResult(
        property_type=property_type,
        total_amount=total_amount,
        my_roles=my_roles,
    )

    roles = _get_roles(property_type)

    # 我方份额 = 应收佣金 × 我方角色占比之和
    my_rate = sum(rate for role, rate in roles.items() if role in my_roles)
    result.my_share = round(total_amount * my_rate, 2)

    # 德佑平台服务费
    result.beike_fee = round(result.my_share * BEIKE_PLATFORM_RATE, 2)

    # 进店业绩
    result.store_income = round(result.my_share - result.beike_fee, 2)

    # 业务员应发佣金
    result.agent_commission = round(result.store_income * AGENT_COMMISSION_RATE, 2)

    # 拆分各业务员应发佣金
    if agent_roles:
        result.agent_shares = calc_agent_shares(
            result.my_share, property_type, my_roles, agent_roles,
        )
    else:
        result.agent_shares = calc_agent_shares(
            result.store_income, property_type, my_roles, None,
        )

    return result
