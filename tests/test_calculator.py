"""佣金计算逻辑的单元测试

验证数据来自 cw-project.md 中的业务案例。
"""

from commission.config import RENTAL, SALE
from commission.calculator import (
    calc_buyer_commission,
    calc_payment_fee,
    calc_seller_commission,
)


class TestPaymentFee:
    """理房通平台费计算"""

    def test_wechat_scan(self):
        assert calc_payment_fee(500, "微信扫码") == 1.5

    def test_wechat_scan_large(self):
        assert calc_payment_fee(10000, "微信扫码") == 30


class TestBuyerCommissionRental:
    """租赁成交人视角

    条件：业主微信扫码500，客户微信扫码500
    角色：录入人(10%)、维护人(10%)、实勘人(10%)、钥匙人(5%) 全部属于其他门店
    成交人占 60%
    """

    def setup_method(self):
        self.result = calc_buyer_commission(
            property_type=RENTAL,
            owner_amount=500,
            owner_payment_method="微信扫码",
            customer_amount=500,
            customer_payment_method="微信扫码",
            my_roles=[],
        )

    def test_payment_fee(self):
        assert self.result.owner_payment_fee == 1.5
        assert self.result.customer_payment_fee == 1.5
        assert self.result.total_payment_fee == 3.0

    def test_owner_role_shares(self):
        d = self.result.owner_detail
        assert d.role_shares["录入人"] == 50.0  # 500 × 10%
        assert d.role_shares["维护人"] == 50.0  # 500 × 10%
        assert d.role_shares["实勘人"] == 50.0  # 500 × 10%
        assert d.role_shares["钥匙人"] == 25.0  # 500 × 5%

    def test_customer_role_shares(self):
        d = self.result.customer_detail
        assert d.role_shares["录入人"] == 50.0
        assert d.role_shares["维护人"] == 50.0
        assert d.role_shares["实勘人"] == 50.0
        assert d.role_shares["钥匙人"] == 25.0

    def test_buyer_received(self):
        # 其他门店: 50+50+50+25=175，成交人: 500-1.5-175=323.5
        assert self.result.owner_received == 323.5
        assert self.result.customer_received == 323.5
        assert self.result.total_received == 647.0

    def test_beike_fee(self):
        assert self.result.beike_fee == 51.76

    def test_store_income(self):
        assert self.result.store_income == 595.24

    def test_agent_commission(self):
        assert self.result.agent_commission == 297.62


class TestBuyerCommissionSale:
    """买卖成交人视角

    条件：业主微信扫码10000，客户微信扫码10000
    角色：录入(10%)、维护(15%)、实勘(2%)、平台实勘(3%)、钥匙(5%)、证件(5%) 全属其他门店/平台
    成交人占 60%
    """

    def setup_method(self):
        self.result = calc_buyer_commission(
            property_type=SALE,
            owner_amount=10000,
            owner_payment_method="微信扫码",
            customer_amount=10000,
            customer_payment_method="微信扫码",
            my_roles=[],
        )

    def test_payment_fee(self):
        assert self.result.owner_payment_fee == 30.0
        assert self.result.customer_payment_fee == 30.0
        assert self.result.total_payment_fee == 60.0

    def test_owner_role_shares(self):
        d = self.result.owner_detail
        assert d.role_shares["录入人"] == 1000.0
        assert d.role_shares["维护人"] == 1500.0
        assert d.role_shares["实勘人"] == 200.0
        assert d.role_shares["平台实勘"] == 300.0
        assert d.role_shares["钥匙人"] == 500.0
        assert d.role_shares["证件人"] == 500.0

    def test_platform_role_share(self):
        # 平台实勘 3% 现作为角色出现在 role_shares 中（替代原 platform_viewing_fee 字段）
        assert self.result.owner_detail.role_shares["平台实勘"] == 300.0
        assert self.result.customer_detail.role_shares["平台实勘"] == 300.0

    def test_buyer_received(self):
        # 10000 - 30 - (1000+1500+200+300+500+500=4000) = 5970
        assert self.result.owner_received == 5970.0
        assert self.result.customer_received == 5970.0
        assert self.result.total_received == 11940.0

    def test_beike_fee(self):
        assert self.result.beike_fee == 955.2

    def test_store_income(self):
        assert self.result.store_income == 10984.8

    def test_agent_commission(self):
        assert self.result.agent_commission == 5492.4


class TestBuyerCommissionRentalAllRoles:
    """租赁成交人兼任全部房源方角色，成交人占比 = 100%"""

    def setup_method(self):
        self.result = calc_buyer_commission(
            property_type=RENTAL,
            owner_amount=1000,
            owner_payment_method="微信扫码",
            customer_amount=1000,
            customer_payment_method="微信扫码",
            my_roles=["录入人", "维护人", "实勘人", "钥匙人"],
        )

    def test_no_other_store_shares(self):
        d = self.result.owner_detail
        assert d.buyer_share == 997.0

    def test_total_received(self):
        assert self.result.total_received == 1994.0


class TestBuyerCommissionRentalPartialRoles:
    """租赁成交人兼任部分房源方角色（录入人+维护人）"""

    def setup_method(self):
        self.result = calc_buyer_commission(
            property_type=RENTAL,
            owner_amount=1000,
            owner_payment_method="微信扫码",
            customer_amount=1000,
            customer_payment_method="微信扫码",
            my_roles=["录入人", "维护人"],
        )

    def test_other_store_shares(self):
        d = self.result.owner_detail
        assert d.role_shares["实勘人"] == 100.0
        assert d.role_shares["钥匙人"] == 50.0

    def test_buyer_received(self):
        # 1000 - 3 - 100 - 50 = 847
        assert self.result.owner_received == 847.0


class TestSellerCommission:
    """房源方视角（它店成交我店房源）"""

    def test_single_role(self):
        result = calc_seller_commission(
            property_type=RENTAL,
            total_amount=1000,
            my_roles=["录入人"],
        )
        assert result.my_share == 100.0
        assert result.beike_fee == 8.0
        assert result.store_income == 92.0
        assert result.agent_commission == 46.0

    def test_multiple_roles(self):
        result = calc_seller_commission(
            property_type=SALE,
            total_amount=10000,
            my_roles=["录入人", "维护人"],
        )
        assert result.my_share == 2500.0
        assert result.beike_fee == 200.0
        assert result.store_income == 2300.0
        assert result.agent_commission == 1150.0


class TestSellerAgentShares:
    """房源方视角：多业务员拆分

    calc_agent_shares 接收 store_income（已扣8%德佑费），
    每人按角色占我方份额的比例分配进店业绩，再直接×50%。
    8%德佑费只扣一次（在总账层面），拆分时不再扣除。
    """

    def test_two_agents(self):
        # 租赁，录入人(10%)张三，维护人(10%)李四
        # my_share = 1000*20% = 200, beike=16, store_income=184
        # 按我方占比分配: 张三=10%/20%=50%, 李四=10%/20%=50%
        result = calc_seller_commission(
            property_type=RENTAL,
            total_amount=1000,
            my_roles=["录入人", "维护人"],
            agent_roles={"录入人": "张三", "维护人": "李四"},
        )
        assert len(result.agent_shares) == 2

        # 张三(10%): 184×(10%/20%)=92, 92×50%=46
        zhang = result.agent_shares[0]
        assert zhang.name == "张三"
        assert zhang.role_rate == 0.10
        assert zhang.my_share == 92.0
        assert zhang.commission == 46.0

        # 李四(10%): 同上
        li = result.agent_shares[1]
        assert li.name == "李四"
        assert li.role_rate == 0.10
        assert li.commission == 46.0

    def test_three_agents(self):
        # 买卖，录入人(10%)张三，维护人(15%)李四，钥匙人(5%)王五
        # my_share = 10000*30% = 3000, beike=240, store_income=2760
        # 按我方占比: 张三=10%/30%, 李四=15%/30%, 王五=5%/30%
        result = calc_seller_commission(
            property_type=SALE,
            total_amount=10000,
            my_roles=["录入人", "维护人", "钥匙人"],
            agent_roles={"录入人": "张三", "维护人": "李四", "钥匙人": "王五"},
        )
        assert len(result.agent_shares) == 3

        # 张三(10%): 2760×(10%/30%)=920, 920×50%=460
        zhang = result.agent_shares[0]
        assert zhang.name == "张三"
        assert zhang.role_rate == 0.10
        assert zhang.commission == 460.0

        # 李四(15%): 2760×(15%/30%)=1380, 1380×50%=690
        li = result.agent_shares[1]
        assert li.name == "李四"
        assert li.role_rate == 0.15
        assert li.commission == 690.0

        # 王五(5%): 2760×(5%/30%)=460, 460×50%=230
        wang = result.agent_shares[2]
        assert wang.name == "王五"
        assert wang.role_rate == 0.05
        assert wang.commission == 230.0


class TestBuyerAgentShares:
    """成交人视角：多业务员拆分

    成交人兼任房源方角色时，角色可能分属不同业务员。
    客源成交人角色自动分配给名为"成交人"的业务员。
    8%德佑费只扣一次（在总账层面），拆分时不再扣除。
    """

    def test_buyer_with_role_agents(self):
        # 租赁，成交人兼任录入人(10%)+维护人(10%)
        # 录入人→张三，维护人→李四，客源成交人(85%)→成交人
        # total_received = 847×2 = 1694
        # beike_fee = 135.52, store_income = 1558.48
        # 录入人份额=200, 扣8%后=184; 维护人份额=200, 扣8%后=184
        # 成交人份额=1694-400=1294, 扣8%后=1190.48
        result = calc_buyer_commission(
            property_type=RENTAL,
            owner_amount=1000,
            owner_payment_method="微信扫码",
            customer_amount=1000,
            customer_payment_method="微信扫码",
            my_roles=["录入人", "维护人"],
            agent_roles={"录入人": "张三", "维护人": "李四"},
        )
        assert len(result.agent_shares) == 3

        # 成交人(85%): 进店1190.48, ×50%=595.24
        buyer = next(s for s in result.agent_shares if s.name == "成交人")
        assert "客源成交人" in buyer.roles
        assert buyer.role_rate == 0.85
        assert buyer.commission == 595.24

        # 张三(10%): 进店184, ×50%=92
        zhang = next(s for s in result.agent_shares if s.name == "张三")
        assert zhang.role_rate == 0.10
        assert zhang.commission == 92.0

        # 李四(10%): 同张三
        li = next(s for s in result.agent_shares if s.name == "李四")
        assert li.role_rate == 0.10
        assert li.commission == 92.0

    def test_no_agent_roles_backward_compat(self):
        # 不传 agent_roles 时，agent_shares 只有一条总记录
        result = calc_seller_commission(
            property_type=RENTAL,
            total_amount=1000,
            my_roles=["录入人"],
        )
        assert len(result.agent_shares) == 1
        assert result.agent_shares[0].commission == 46.0


class TestPlatformViewingRole:
    """平台实勘是平台角色，永不属门店：
    即便误传进 my_roles，也不应被算作我方或分给业务员。
    """

    def test_platform_role_in_my_roles_ignored(self):
        # 误传 my_roles=["平台实勘"]，成交人份额应仍为 5970（平台 3% 不归成交人）
        result = calc_buyer_commission(
            property_type=SALE,
            owner_amount=10000,
            owner_payment_method="微信扫码",
            customer_amount=10000,
            customer_payment_method="微信扫码",
            my_roles=["平台实勘"],
        )
        assert result.owner_received == 5970.0
        assert result.total_received == 11940.0

    def test_platform_role_not_assigned_to_agent(self):
        # 误把平台实勘指派给业务员，agent_shares 不应包含该业务员
        result = calc_buyer_commission(
            property_type=SALE,
            owner_amount=10000,
            owner_payment_method="微信扫码",
            customer_amount=10000,
            customer_payment_method="微信扫码",
            my_roles=["平台实勘"],
            agent_roles={"平台实勘": "张三"},
        )
        names = [s.name for s in result.agent_shares]
        assert "张三" not in names

    def test_seller_platform_role_in_my_roles_ignored(self):
        # 房源方视角误传 my_roles=["平台实勘"]：平台角色被入口防御剔除，
        # 我方份额应为 0，且平台角色不会分给业务员
        result = calc_seller_commission(
            property_type=SALE,
            total_amount=10000,
            my_roles=["平台实勘"],
            agent_roles={"平台实勘": "张三"},
        )
        assert result.my_share == 0.0
        names = [s.name for s in result.agent_shares]
        assert "张三" not in names


class TestAgentShareConsistency:
    """业务员拆分合计应与总账保持一致。"""

    def test_buyer_split_totals_match_result_totals(self):
        result = calc_buyer_commission(
            property_type=RENTAL,
            owner_amount=1000,
            owner_payment_method="微信扫码",
            customer_amount=1000,
            customer_payment_method="微信扫码",
            my_roles=["录入人", "维护人"],
            agent_roles={"录入人": "张三", "维护人": "李四"},
        )

        assert sum(share.my_share for share in result.agent_shares) == result.store_income
        assert sum(share.commission for share in result.agent_shares) == result.agent_commission
        assert sum(share.beike_fee for share in result.agent_shares) == 0.0

    def test_seller_split_totals_match_result_totals(self):
        result = calc_seller_commission(
            property_type=SALE,
            total_amount=10000,
            my_roles=["录入人", "维护人", "钥匙人"],
            agent_roles={"录入人": "张三", "维护人": "李四", "钥匙人": "王五"},
        )

        assert sum(share.my_share for share in result.agent_shares) == result.store_income
        assert sum(share.commission for share in result.agent_shares) == result.agent_commission
        assert sum(share.beike_fee for share in result.agent_shares) == 0.0

    def test_buyer_and_seller_split_helpers_are_available(self):
        from commission import calculator

        assert callable(calculator.calc_buyer_agent_shares)
        assert callable(calculator.calc_seller_agent_shares)
