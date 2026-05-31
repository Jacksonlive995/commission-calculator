"""佣金记录转换。"""

from dataclasses import dataclass, field

from commission.calculator import BuyerCommissionResult, SellerCommissionResult


@dataclass
class CommissionRecord:
    """一条佣金记录，用于写入外部系统。"""

    agent_name: str = ""
    view: str = "buyer"
    property_type: str = "rental"
    roles: list[str] = field(default_factory=list)
    role_rate: float = 0.0
    total_amount: float = 0.0
    my_share: float = 0.0
    beike_fee: float = 0.0
    store_income: float = 0.0
    commission: float = 0.0


def _records_from_buyer_result(
    result: BuyerCommissionResult,
    property_type: str,
    total_amount: float,
) -> list[CommissionRecord]:
    records: list[CommissionRecord] = []

    for share in result.agent_shares:
        name = share.name or "业务员"
        records.append(CommissionRecord(
            agent_name=name,
            view="buyer",
            property_type=property_type,
            roles=share.roles,
            role_rate=share.role_rate,
            total_amount=total_amount,
            my_share=share.my_share,
            beike_fee=share.beike_fee,
            store_income=share.store_income,
            commission=share.commission,
        ))
    return records


def _records_from_seller_result(
    result: SellerCommissionResult,
    property_type: str,
    total_amount: float,
) -> list[CommissionRecord]:
    records: list[CommissionRecord] = []

    for share in result.agent_shares:
        name = share.name or "业务员"
        records.append(CommissionRecord(
            agent_name=name,
            view="seller",
            property_type=property_type,
            roles=share.roles,
            role_rate=share.role_rate,
            total_amount=total_amount,
            my_share=share.my_share,
            beike_fee=share.beike_fee,
            store_income=share.store_income,
            commission=share.commission,
        ))
    return records


def extract_records(
    result,
    view: str,
    property_type: str,
    total_amount: float = 0.0,
) -> list[CommissionRecord]:
    if isinstance(result, BuyerCommissionResult):
        return _records_from_buyer_result(result, property_type, total_amount)
    if isinstance(result, SellerCommissionResult):
        return _records_from_seller_result(result, property_type, total_amount)
    return []
