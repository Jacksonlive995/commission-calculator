"""GUI 结果展示的回归测试

需要 QApplication，使用 offscreen 平台避免依赖显示器。
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from commission.calculator import calc_buyer_commission, calc_seller_commission
from commission.config import RENTAL, SALE
from commission.gui.steps.step_result import StepResult


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestAgentSplitBox:
    """业务员佣金拆分框应是一个完整闭合的方框（单个 ┌ + 单个 └），
    无论有多少个业务员。
    """

    def test_buyer_three_agents_single_box(self, qapp):
        # 租赁成交人兼任录入人+维护人，分属张三、李四，客源成交人自动归"成交人"
        result = calc_buyer_commission(
            property_type=RENTAL,
            owner_amount=1000,
            owner_payment_method="微信扫码",
            customer_amount=1000,
            customer_payment_method="微信扫码",
            my_roles=["录入人", "维护人"],
            agent_roles={"录入人": "张三", "维护人": "李四"},
        )
        assert len(result.agent_shares) == 3  # 张三、李四、成交人

        text = StepResult()._format_buyer(result)

        assert text.count("┌") == 1
        assert text.count("└") == 1

    def test_seller_three_agents_single_box(self, qapp):
        # 买卖房源方，三个角色分属三人
        result = calc_seller_commission(
            property_type=SALE,
            total_amount=10000,
            my_roles=["录入人", "维护人", "钥匙人"],
            agent_roles={"录入人": "张三", "维护人": "李四", "钥匙人": "王五"},
        )
        assert len(result.agent_shares) == 3

        text = StepResult()._format_seller(result)

        assert text.count("┌") == 1
        assert text.count("└") == 1


def test_sale_role_checkboxes_exclude_platform(qapp):
    """买卖角色勾选列表不应包含平台实勘，但保留其它门店角色。"""
    from commission.gui.steps.step_roles import StepRoles

    sr = StepRoles()
    sr.setup({"property_type": SALE, "view": "buyer"})

    labels = [cb.text() for cb in sr._checkboxes]
    assert all("平台实勘" not in label for label in labels)
    assert any("录入人" in label for label in labels)
    assert "平台实勘" not in sr._role_names


def test_buyer_result_marks_platform_role(qapp):
    """买卖成交人结果中，平台实勘应标注（平台收取），而非（它店）。"""
    result = calc_buyer_commission(
        property_type=SALE,
        owner_amount=10000,
        owner_payment_method="微信扫码",
        customer_amount=10000,
        customer_payment_method="微信扫码",
        my_roles=[],
    )
    text = StepResult()._format_buyer(result)
    assert "平台实勘 300.00（平台收取）" in text
    assert "平台实勘 300.00（它店）" not in text
