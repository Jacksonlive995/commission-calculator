"""运行配置读取。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_dotenv() -> Path | None:
    candidates: list[Path] = []
    candidates.append(Path(__file__).resolve().parent.parent.parent / ".env")
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / ".env")
    candidates.append(Path.cwd() / ".env")
    for path in candidates:
        if path.exists():
            return path
    return None


_dotenv = _find_dotenv()
if _dotenv:
    for line in _dotenv.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

FEISHU_APP_ID: str = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET: str = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_API_BASE: str = "https://open.feishu.cn/open-apis"
