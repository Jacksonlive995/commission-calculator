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

# ── 飞书多维表格 ────────────────────────────────────────────
import os
import sys
from pathlib import Path


def _find_dotenv() -> Path | None:
    """查找 .env 文件：项目根目录 > exe同级目录 > 当前工作目录"""
    candidates: list[Path] = []
    # 开发模式：项目根目录（src/commission/config.py → 上3级）
    candidates.append(Path(__file__).resolve().parent.parent.parent / ".env")
    # PyInstaller 打包模式：exe 同级目录
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / ".env")
    # 当前工作目录
    candidates.append(Path.cwd() / ".env")
    for p in candidates:
        if p.exists():
            return p
    return None


_dotenv = _find_dotenv()
if _dotenv:
    for _line in _dotenv.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _k, _v = _k.strip(), _v.strip()
            if _k and _k not in os.environ:
                os.environ[_k] = _v

FEISHU_APP_ID: str = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET: str = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_API_BASE: str = "https://open.feishu.cn/open-apis"
