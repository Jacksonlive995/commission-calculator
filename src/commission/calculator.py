"""佣金计算核心逻辑

所有函数都是纯函数，不涉及IO操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from commission.config import (
    AGENT_COMMISSION_RATE,
    BEIKE_PLATFORM_RATE,
    PAYMENT_RATES,
    PLATFORM_ROLES,
    RENTAL,
    RENTAL_ROLES,
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


def _single_total_share(total_share: float, roles: dict[str, float], my_roles: list[str]) -> list[AgentShare]:
    return [AgentShare(
        name="",
        roles=my_roles[:],
        role_rate=sum(rate for role, rate in roles.items() if role in my_roles),
        my_share=total_share,
        beike_fee=0.0,
        store_income=total_share,
        commission=round(total_share * AGENT_COMMISSION_RATE, 2),
    )]


def _shares_from_role_amounts(
    role_shares_in_store: dict[str, float],
    role_rates: dict[str, float],
    agent_roles: dict[str, str],
) -> list[AgentShare]:
    agent_map: dict[str, list[str]] = {}
    for role, name in agent_roles.items():
        if role in role_shares_in_store:
            agent_map.setdefault(name, []).append(role)

    shares: list[AgentShare] = []
    for name, role_list in agent_map.items():
        my_share = round(sum(role_shares_in_store[role] for role in role_list), 2)
        shares.append(AgentShare(
            name=name,
            roles=role_list,
            role_rate=sum(role_rates[role] for role in role_list),
            my_share=my_share,
            beike_fee=0.0,
            store_income=my_share,
            commission=round(my_share * AGENT_COMMISSION_RATE, 2),
        ))
    return shares


def calc_buyer_agent_shares(
    property_type: str,
    my_roles: list[str],
    agent_roles: dict[str, str] | None,
    store_income: float,
    buyer_rate: float,
    buyer_received: float,
    total_amount: float,
) -> list[AgentShare]:
    roles = _get_roles(property_type)
    if not agent_roles:
        return _single_total_share(store_income, roles, my_roles)

    role_rates: dict[str, float] = dict(roles)
    role_rates["客源成交人"] = buyer_rate

    role_shares_in_store: dict[str, float] = {}
    my_role_gross = 0.0
    for role in my_roles:
        gross = round(total_amount * role_rates[role], 2)
        my_role_gross += gross
        role_shares_in_store[role] = round(gross * (1 - BEIKE_PLATFORM_RATE), 2)

    buyer_gross = round(buyer_received - my_role_gross, 2)
    role_shares_in_store["客源成交人"] = round(buyer_gross * (1 - BEIKE_PLATFORM_RATE), 2)
    return _shares_from_role_amounts(role_shares_in_store, role_rates, agent_roles)


def calc_seller_agent_shares(
    property_type: str,
    my_roles: list[str],
    agent_roles: dict[str, str] | None,
    store_income: float,
) -> list[AgentShare]:
    roles = _get_roles(property_type)
    if not agent_roles:
        return _single_total_share(store_income, roles, my_roles)

    my_rate = sum(roles[role] for role in my_roles)
    role_shares_in_store = {
        role: round(store_income * (roles[role] / my_rate), 2)
        for role in my_roles
    }
    return _shares_from_role_amounts(role_shares_in_store, roles, agent_roles)


def calc_agent_shares(
    total_share: float,
    property_type: str,
    my_roles: list[str],
    agent_roles: dict[str, str] | None = None,
    buyer_rate: float | None = None,
    buyer_received: float | None = None,
    total_amount: float | None = None,
) -> list[AgentShare]:
    """按角色拆分各业务员应得佣金"""
    if buyer_rate is not None and buyer_received is not None and total_amount is not None:
        return calc_buyer_agent_shares(
            property_type,
            my_roles,
            agent_roles,
            total_share,
            buyer_rate,
            buyer_received,
            total_amount,
        )
    return calc_seller_agent_shares(property_type, my_roles, agent_roles, total_share)


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
    my_roles = [r for r in my_roles if r not in PLATFORM_ROLES]
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
            result.store_income, property_type, my_roles, full_agent_roles,
            buyer_rate=buyer_rate,
            buyer_received=result.total_received,
            total_amount=owner_amount + customer_amount,
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
    my_roles = [r for r in my_roles if r not in PLATFORM_ROLES]
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
            result.store_income, property_type, my_roles, agent_roles,
        )
    else:
        result.agent_shares = calc_agent_shares(
            result.store_income, property_type, my_roles, None,
        )

    return result
