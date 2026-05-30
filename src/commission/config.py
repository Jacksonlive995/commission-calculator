"""佣金计算器配置常量"""

# 房源类型
RENTAL = "rental"  # 租赁
SALE = "sale"  # 买卖

# 支付方式 → 理房通费率
PAYMENT_RATES: dict[str, float] = {
    "微信小程序": 0.0065,
    "微信APP": 0.0065,
    "微信扫码": 0.003,
    "支付宝APP": 0.003,
    "支付宝扫码": 0.003,
    "快捷支付": 0.004,
    "银联线上支付": 0.0055,
    "京东白条": 0.003,
}

# 支付方式快捷编号
PAYMENT_OPTIONS: list[str] = list(PAYMENT_RATES.keys())

# 租赁房源角色 → 占比
RENTAL_ROLES: dict[str, float] = {
    "录入人": 0.10,
    "维护人": 0.10,
    "实勘人": 0.10,
    "钥匙人": 0.05,
}

# 买卖房源角色 → 占比
SALE_ROLES: dict[str, float] = {
    "录入人": 0.10,
    "维护人": 0.15,
    "实勘人": 0.02,
    "平台实勘": 0.03,  # 平台收取（VR 拍摄），永不属门店
    "钥匙人": 0.05,
    "证件人": 0.05,
}

# 平台角色集合：永不属门店、不可勾选、不参与业务员拆分
PLATFORM_ROLES: frozenset[str] = frozenset({"平台实勘"})

# 贝壳/德佑平台服务费率
BEIKE_PLATFORM_RATE: float = 0.08

# 业务员提成比例
AGENT_COMMISSION_RATE: float = 0.50
