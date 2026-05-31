"""飞书多维表格 API 封装

负责认证、表格创建、记录写入。
首次使用时自动创建多维表格及数据表，后续写入复用已有表格。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from commission.records import CommissionRecord
from commission.settings import FEISHU_API_BASE, FEISHU_APP_ID, FEISHU_APP_SECRET

# ── 本地配置文件路径 ─────────────────────────────────────────

_CONFIG_DIR = Path.home() / ".commission"
_CONFIG_FILE = _CONFIG_DIR / "feishu_config.json"


def _load_local_config() -> dict:
    if _CONFIG_FILE.exists():
        return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def _save_local_config(cfg: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


# ── HTTP 请求 ─────────────────────────────────────────────────


def _request(
    method: str,
    path: str,
    token: str | None = None,
    body: dict | None = None,
    max_retries: int = 3,
    return_data: bool = True,
) -> dict:
    """发送飞书 API 请求，带简单重试

    return_data: True 则返回 result["data"]，False 则返回完整 result
    """
    url = f"{FEISHU_API_BASE}{path}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    req = Request(url, data=data, headers=headers, method=method)

    for attempt in range(max_retries):
        try:
            with urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("code") != 0:
                    raise FeishuError(result.get("code", -1), result.get("msg", "unknown"))
                return result.get("data", {}) if return_data else result
        except HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
            raise FeishuError(e.code, f"HTTP {e.code}: {body_text[:200]}") from e


class FeishuError(Exception):
    def __init__(self, code: int, msg: str) -> None:
        self.code = code
        super().__init__(f"飞书API错误({code}): {msg}")


# ── 认证 ─────────────────────────────────────────────────────

_token_cache: dict = {"token": "", "expire_at": 0.0}


def _get_token() -> str:
    """获取 tenant_access_token，带2小时缓存"""
    if _token_cache["token"] and time.time() < _token_cache["expire_at"]:
        return _token_cache["token"]

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        raise FeishuError(-1, "请先配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET（参见 .env.example）")

    data = _request("POST", "/auth/v3/tenant_access_token/internal", body={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET,
    }, return_data=False)
    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expire_at"] = time.time() + data.get("expire", 7200) - 60
    return _token_cache["token"]


# ── 多维表格结构定义 ──────────────────────────────────────────

# 佣金记录字段定义
_COMMISSION_FIELDS = [
    {"field_name": "日期", "type": 5},
    {"field_name": "房源类型", "type": 3, "property": {
        "options": [{"name": "租赁"}, {"name": "买卖"}]
    }},
    {"field_name": "角色", "type": 1},             # text
    {"field_name": "角色占比", "type": 2},            # number (0.10 = 10%)
    {"field_name": "佣金总额", "type": 2},          # number
    {"field_name": "我方份额", "type": 2},          # number
    {"field_name": "德佑费", "type": 2},            # number
    {"field_name": "进店业绩", "type": 2},          # number
    {"field_name": "应发佣金", "type": 2},          # number
]


def _table_name(name: str, view: str) -> str:
    """生成数据表名称：张三_成交方 / 张三_客源方"""
    suffix = "成交方" if view == "buyer" else "客源方"
    return f"{name}_{suffix}"


# ── 多维表格创建 ─────────────────────────────────────────────


def _create_app(token: str) -> str:
    """创建多维表格应用，返回 app_token"""
    data = _request("POST", "/bitable/v1/apps", token, {"name": "佣金统计"})
    return data["app"]["app_token"]


def _create_table(token: str, app_token: str, table_name: str) -> str:
    """在多维表格中创建数据表，返回 table_id"""
    data = _request(
        "POST",
        f"/bitable/v1/apps/{app_token}/tables",
        token,
        {"table": {"name": table_name, "fields": _COMMISSION_FIELDS}},
    )
    return data["table_id"]


def _list_tables(token: str, app_token: str) -> dict[str, str]:
    """列出多维表格中所有数据表，返回 {表名: table_id}"""
    tables: dict[str, str] = {}
    page_token = None
    while True:
        path = f"/bitable/v1/apps/{app_token}/tables?page_size=100"
        if page_token:
            path += f"&page_token={page_token}"
        data = _request("GET", path, token)
        for t in data.get("items", []):
            tables[t["name"]] = t["table_id"]
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return tables


# ── 记录写入 ──────────────────────────────────────────────────


def _create_record(token: str, app_token: str, table_id: str, fields: dict) -> None:
    """向数据表写入一条记录"""
    _request(
        "POST",
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        token,
        {"fields": fields},
    )


# ── 公开接口 ──────────────────────────────────────────────────


def write_to_feishu(records: list[CommissionRecord]) -> str:
    """将佣金记录写入飞书多维表格

    返回多维表格的 URL。
    首次调用自动创建表格和数据表，后续复用。
    """
    token = _get_token()

    # 读取或创建多维表格
    cfg = _load_local_config()
    app_token = cfg.get("app_token", "")

    if not app_token:
        app_token = _create_app(token)
        cfg["app_token"] = app_token
        cfg["tables"] = {}
        _save_local_config(cfg)

    # 获取已有数据表
    existing_tables = cfg.get("tables", {})
    # 同步一次远端（防止手动删除了数据表）
    remote_tables = _list_tables(token, app_token)
    existing_tables.update(remote_tables)

    # 按业务员+视角分组写入
    now_ms = int(time.time() * 1000)
    type_label = {"rental": "租赁", "sale": "买卖"}

    for record in records:
        table_name = _table_name(record.agent_name, record.view)

        # 确保数据表存在
        if table_name not in existing_tables:
            table_id = _create_table(token, app_token, table_name)
            existing_tables[table_name] = table_id
            cfg["tables"] = existing_tables
            _save_local_config(cfg)
        else:
            table_id = existing_tables[table_name]

        # 写入记录
        fields = {
            "日期": now_ms,
            "房源类型": type_label.get(record.property_type, record.property_type),
            "角色": " + ".join(record.roles) if record.roles else "全部",
            "角色占比": record.role_rate,
            "佣金总额": record.total_amount,
            "我方份额": record.my_share,
            "德佑费": record.beike_fee,
            "进店业绩": record.store_income,
            "应发佣金": record.commission,
        }
        _create_record(token, app_token, table_id, fields)

    # 更新本地配置
    cfg["tables"] = existing_tables
    _save_local_config(cfg)

    return f"https://feishu.cn/base/{app_token}"
