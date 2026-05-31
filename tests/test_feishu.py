"""飞书多维表格模块的单元测试

使用 mock 替代真实 API 调用。
"""

from unittest.mock import patch

from commission.calculator import calc_buyer_commission, calc_seller_commission
from commission.config import RENTAL, SALE
from commission.feishu import (
    CommissionRecord,
    FeishuError,
    _table_name,
    extract_records,
    write_to_feishu,
)


class TestTableName:
    """数据表命名"""

    def test_buyer_view(self):
        assert _table_name("张三", "buyer") == "张三_成交方"

    def test_seller_view(self):
        assert _table_name("李四", "seller") == "李四_客源方"


class TestExtractRecords:
    """从计算结果提取佣金记录"""

    def test_buyer_result(self):
        result = calc_buyer_commission(
            property_type=RENTAL,
            owner_amount=1000,
            owner_payment_method="微信扫码",
            customer_amount=1000,
            customer_payment_method="微信扫码",
            my_roles=["录入人", "维护人"],
            agent_roles={"录入人": "张三", "维护人": "李四"},
        )
        records = extract_records(result, "buyer", RENTAL, 2000.0)
        assert len(records) == 3
        names = [r.agent_name for r in records]
        assert "成交人" in names
        assert "张三" in names
        assert "李四" in names
        for r in records:
            assert r.view == "buyer"
            assert r.property_type == RENTAL

    def test_seller_result(self):
        result = calc_seller_commission(
            property_type=SALE,
            total_amount=10000,
            my_roles=["录入人", "维护人"],
            agent_roles={"录入人": "张三", "维护人": "李四"},
        )
        records = extract_records(result, "seller", SALE)
        assert len(records) == 2
        names = [r.agent_name for r in records]
        assert "张三" in names
        assert "李四" in names
        for r in records:
            assert r.view == "seller"
            assert r.property_type == SALE

    def test_no_agent_roles(self):
        result = calc_seller_commission(
            property_type=RENTAL,
            total_amount=1000,
            my_roles=["录入人"],
        )
        records = extract_records(result, "seller", RENTAL)
        assert len(records) == 1
        assert records[0].agent_name == "业务员"


class TestWriteToFeishu:
    """写入飞书多维表格（mock API 调用）"""

    @patch("commission.feishu._save_local_config")
    @patch("commission.feishu._load_local_config")
    @patch("commission.feishu._request")
    @patch("commission.feishu._get_token")
    def test_first_write_creates_app_and_tables(self, mock_token, mock_request, mock_load, mock_save):
        """首次写入：创建多维表格 + 数据表 + 记录"""
        mock_token.return_value = "fake_token"
        mock_load.return_value = {}
        call_count = 0

        def fake_request(method, path, token=None, body=None, max_retries=3):
            nonlocal call_count
            call_count += 1
            if path.endswith("/apps") and method == "POST":
                return {"app": {"app_token": "new_app_token"}}
            if "/tables" in path and method == "POST":
                return {"table_id": "new_table_id"}
            if "/tables" in path and method == "GET":
                return {"items": []}
            if "/records" in path and method == "POST":
                return {"record": {}}
            return {}

        mock_request.side_effect = fake_request

        records = [CommissionRecord(
            agent_name="张三", view="buyer", property_type=RENTAL,
            roles=["录入人"], role_rate=0.10,
            total_amount=2000, my_share=184, beike_fee=0,
            store_income=184, commission=92,
        )]

        url = write_to_feishu(records)
        assert "new_app_token" in url
        assert call_count >= 3  # 列表 + 创建表 + 写入记录
        mock_save.assert_called()

    @patch("commission.feishu._save_local_config")
    @patch("commission.feishu._load_local_config")
    @patch("commission.feishu._request")
    @patch("commission.feishu._get_token")
    def test_subsequent_write_reuses_app(self, mock_token, mock_request, mock_load, mock_save):
        """后续写入：复用已有表格，只创建新数据表"""
        mock_token.return_value = "fake_token"
        mock_load.return_value = {
            "app_token": "existing_app",
            "tables": {"张三_成交方": "existing_table"},
        }

        def fake_request(method, path, token=None, body=None, max_retries=3):
            if "/tables" in path and method == "GET":
                return {"items": [{"name": "张三_成交方", "table_id": "existing_table"}]}
            if "/records" in path and method == "POST":
                return {"record": {}}
            return {}

        mock_request.side_effect = fake_request

        records = [CommissionRecord(
            agent_name="张三", view="buyer", property_type=RENTAL,
            roles=["录入人"], role_rate=0.10,
            total_amount=2000, my_share=184, beike_fee=0,
            store_income=184, commission=92,
        )]

        url = write_to_feishu(records)
        assert "existing_app" in url

    @patch("commission.feishu._load_local_config")
    @patch("commission.feishu._get_token")
    def test_api_error_raises_feishu_error(self, mock_token, mock_load):
        """API 返回错误时抛出 FeishuError"""
        mock_token.return_value = "fake_token"
        mock_load.return_value = {"app_token": "existing_app", "tables": {}}

        with patch("commission.feishu._request", side_effect=FeishuError(99999, "权限不足")):
            records = [CommissionRecord(agent_name="张三", view="buyer")]
            try:
                write_to_feishu(records)
                assert False, "Should have raised"
            except FeishuError as e:
                assert "权限不足" in str(e)
