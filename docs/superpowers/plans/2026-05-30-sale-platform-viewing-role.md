# 买卖「平台实勘 3%」改为独立角色 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把买卖房源被平台分走的 3% 平台实勘费建模为一个独立角色，使成交人份额从总额的 63% 修正为 60%。

**Architecture:** 在 `SALE_ROLES` 中新增「平台实勘 3%」角色，并用 `PLATFORM_ROLES` 常量标记它为「永不属门店」。核心计算公式因此天然正确（平台角色自动归入「非我方」被扣除）；特判只集中在输入侧（不可勾选）、展示侧（标注「平台收取」）和一道入口防御。

**Tech Stack:** Python 3.12、pytest、PySide6（GUI）、uv（依赖/运行）、ruff（F401 检查）。

**对应 spec:** `docs/superpowers/specs/2026-05-30-sale-platform-viewing-role-design.md`

---

## File Structure

| 文件 | 职责 | 本次改动 |
|------|------|----------|
| `src/commission/config.py` | 费率/角色常量 | SALE_ROLES 加平台实勘；新增 PLATFORM_ROLES；删 SALE_PLATFORM_VIEWING_RATE |
| `src/commission/calculator.py` | 纯计算逻辑 | 删 platform_viewing_fee 字段与计算段；入口防御过滤 my_roles |
| `src/commission/cli.py` | CLI 交互+展示 | role_names 过滤平台角色；展示标注三分支；删旧平台费展示行 |
| `src/commission/gui/steps/step_roles.py` | GUI 角色勾选 | 勾选列表排除平台角色 |
| `src/commission/gui/steps/step_result.py` | GUI 结果展示 | 展示标注三分支；删旧平台费展示行 |
| `tests/test_calculator.py` | 计算单测 | 更新 sale 期望值；新增平台角色回归测试 |
| `tests/test_gui.py` | GUI 单测 | 新增「勾选列表排除平台角色」「展示标注」测试 |

执行顺序：Task 1（核心数值）→ Task 2（入口防御）→ Task 3（输入侧）→ Task 4（展示侧）。

---

## Task 1: 平台实勘建模为角色，修正成交人份额

**Files:**
- Modify: `src/commission/config.py`
- Modify: `src/commission/calculator.py`
- Modify: `src/commission/cli.py`（删旧平台费展示行）
- Modify: `src/commission/gui/steps/step_result.py`（删旧平台费展示行）
- Test: `tests/test_calculator.py`

- [ ] **Step 1: 更新 sale 测试期望值（写失败测试）**

把 `tests/test_calculator.py` 中整个 `TestBuyerCommissionSale` 类替换为：

```python
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
```

- [ ] **Step 2: 跑测试验证失败**

Run: `uv run pytest tests/test_calculator.py::TestBuyerCommissionSale -v`
Expected: FAIL — `test_owner_role_shares`/`test_platform_role_share` 因 `role_shares` 无 `"平台实勘"` 键报 `KeyError`；`test_buyer_received` 等因当前算 6270 而非 5970 报 `AssertionError`。

- [ ] **Step 3: 修改 `config.py` 新增平台角色**

把 `SALE_ROLES` 定义和其后的 `SALE_PLATFORM_VIEWING_RATE` 替换为：

```python
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
```

（删除原 `SALE_PLATFORM_VIEWING_RATE: float = 0.03` 一行。）

- [ ] **Step 4: 修改 `calculator.py` 删除独立平台费**

a) 顶部 import 块改为（删 `SALE_PLATFORM_VIEWING_RATE` 和不再使用的 `SALE`）：

```python
from commission.config import (
    AGENT_COMMISSION_RATE,
    BEIKE_PLATFORM_RATE,
    PAYMENT_RATES,
    RENTAL,
    RENTAL_ROLES,
    SALE_ROLES,
)
```

b) `PaymentDetail` 数据类删除 `platform_viewing_fee` 字段（删掉这一行）：

```python
    platform_viewing_fee: float = 0.0
```

c) `calc_buyer_commission` 的 Step 2&3 循环中，删除以下整段（不再单独计算平台费）：

```python
        # 平台实勘费（仅买卖），由平台直接收取，不从成交人份额中扣除
        if property_type == SALE:
            detail.platform_viewing_fee = round(amount * SALE_PLATFORM_VIEWING_RATE, 2)
```

保留的 `role_shares` 循环会天然把「平台实勘」计入 `role_shares` 且（因不在 `my_roles`）计入 `other_store_shares`，成交人份额自动变为 60%。

- [ ] **Step 5: 删除 CLI/GUI 中引用已删字段的展示行**

`src/commission/cli.py` `_show_buyer_result` 中删除：

```python
        if detail.platform_viewing_fee > 0:
            print(f"      平台实勘  {_fmt_money(detail.platform_viewing_fee)}（平台收取）")
```

`src/commission/gui/steps/step_result.py` `_format_buyer` 中删除：

```python
            if detail.platform_viewing_fee > 0:
                lines.append(f"   平台实勘 {f(detail.platform_viewing_fee)}（平台收取）")
```

（平台实勘现已作为普通角色出现在 Step 2 的 `role_shares` 遍历中，无需单独打印。）

- [ ] **Step 6: 跑全量测试验证通过**

Run: `uv run pytest -q`
Expected: PASS（28 项全过；sale 相关断言现在匹配修正后的数值）。

- [ ] **Step 7: 验证 CLI/GUI 不再引用已删字段**

Run:
```bash
uv run python -c "import importlib; [importlib.import_module(m) for m in ['commission.cli','commission.gui.steps.step_result']]; print('import OK')"
grep -rn "platform_viewing_fee\|SALE_PLATFORM_VIEWING_RATE" src/ tests/ || echo "无遗留引用"
```
Expected: 打印 `import OK` 且 `无遗留引用`。

- [ ] **Step 8: ruff 检查无新增未使用 import**

Run: `uvx ruff check --select F401 src/ tests/`
Expected: `All checks passed!`

- [ ] **Step 9: 提交**

```bash
git add src/commission/config.py src/commission/calculator.py src/commission/cli.py src/commission/gui/steps/step_result.py tests/test_calculator.py
git commit -m "fix: model sale platform-viewing 3% as a role so buyer share is 60%"
```

---

## Task 2: 入口防御 — 平台角色误入 my_roles 也不算错

**Files:**
- Modify: `src/commission/calculator.py`
- Test: `tests/test_calculator.py`

- [ ] **Step 1: 新增回归测试（写失败测试）**

在 `tests/test_calculator.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 跑测试验证失败**

Run: `uv run pytest tests/test_calculator.py::TestPlatformViewingRole -v`
Expected: FAIL — 未做入口防御时，`my_roles=["平台实勘"]` 会把平台实勘当我方角色，`owner_received` 算成 6270.0（≠5970.0）。

- [ ] **Step 3: 加入口防御**

`src/commission/calculator.py` 顶部 import 块加入 `PLATFORM_ROLES`：

```python
from commission.config import (
    AGENT_COMMISSION_RATE,
    BEIKE_PLATFORM_RATE,
    PAYMENT_RATES,
    PLATFORM_ROLES,
    RENTAL,
    RENTAL_ROLES,
    SALE_ROLES,
)
```

在 `calc_buyer_commission` 函数体第一行（docstring 之后、`result = ...` 之前）加入：

```python
    my_roles = [r for r in my_roles if r not in PLATFORM_ROLES]
```

在 `calc_seller_commission` 函数体第一行（docstring 之后、`result = ...` 之前）加入同样一行：

```python
    my_roles = [r for r in my_roles if r not in PLATFORM_ROLES]
```

- [ ] **Step 4: 跑全量测试验证通过**

Run: `uv run pytest -q`
Expected: PASS（30 项全过）。

- [ ] **Step 5: 提交**

```bash
git add src/commission/calculator.py tests/test_calculator.py
git commit -m "fix: guard against platform roles leaking into my_roles"
```

---

## Task 3: 输入侧 — 平台实勘不可勾选/选择

**Files:**
- Modify: `src/commission/gui/steps/step_roles.py`
- Modify: `src/commission/cli.py`
- Test: `tests/test_gui.py`

- [ ] **Step 1: 新增 GUI 测试（写失败测试）**

在 `tests/test_gui.py` 末尾追加：

```python
def test_sale_role_checkboxes_exclude_platform(qapp):
    """买卖角色勾选列表不应包含平台实勘，但保留其它门店角色。"""
    from commission.gui.steps.step_roles import StepRoles

    sr = StepRoles()
    sr.setup({"property_type": SALE, "view": "buyer"})

    labels = [cb.text() for cb in sr._checkboxes]
    assert all("平台实勘" not in label for label in labels)
    assert any("录入人" in label for label in labels)
    assert "平台实勘" not in sr._role_names
```

- [ ] **Step 2: 跑测试验证失败**

Run: `uv run pytest tests/test_gui.py::test_sale_role_checkboxes_exclude_platform -v`
Expected: FAIL — 当前 `SALE_ROLES` 含平台实勘，勾选列表与 `_role_names` 都会包含它。

- [ ] **Step 3: 修改 `step_roles.py` 排除平台角色**

a) import 加入 `PLATFORM_ROLES`：

```python
from commission.config import PLATFORM_ROLES, RENTAL, RENTAL_ROLES, SALE_ROLES
```

b) `setup` 方法中，把构建 `_role_names` 与勾选框的部分改为（过滤平台角色，并保持 `_role_names` 与 `_checkboxes` 一一对应）：

```python
        self._role_names = [r for r in roles if r not in PLATFORM_ROLES]

        # 清除旧复选框
        while self._cb_layout.count():
            item = self._cb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if is_buyer:
            self.lbl_hint.setText("本店业务员兼任哪些房源方角色？")
        else:
            self.lbl_hint.setText("本店业务员拥有哪些房源方角色？")

        self._checkboxes: list[QCheckBox] = []
        for role in self._role_names:
            pct = int(roles[role] * 100)
            cb = QCheckBox(f"{role}（{pct}%）")
            self._cb_layout.addWidget(cb)
            self._checkboxes.append(cb)
```

（注意：原代码先 `self._role_names = list(roles.keys())` 再在循环里 `roles.items()`；改后统一以过滤后的 `_role_names` 驱动，确保 `get_state` 的 `zip(self._role_names, self._checkboxes)` 仍对齐。）

- [ ] **Step 4: 修改 `cli.py` 的 role_names**

a) import 加入 `PLATFORM_ROLES`：

```python
from commission.config import (
    PAYMENT_OPTIONS,
    PAYMENT_RATES,
    PLATFORM_ROLES,
    RENTAL,
    RENTAL_ROLES,
    SALE,
    SALE_ROLES,
)
```

b) `main()` 中构建 `role_names` 的那一行替换为：

```python
    all_roles = RENTAL_ROLES if property_type == RENTAL else SALE_ROLES
    role_names = [r for r in all_roles if r not in PLATFORM_ROLES]
```

（「全部属于本店 / 全部不属于本店 / 逐个选择」三分支都基于过滤后的 `role_names`，故均不会纳入平台实勘。）

- [ ] **Step 5: 跑相关测试与全量测试验证通过**

Run: `uv run pytest -q`
Expected: PASS（31 项全过）。

- [ ] **Step 6: 手动核对 CLI（可选但推荐）**

Run: `uv run commission`，选择「买卖 → 成交人」，确认角色勾选/询问列表中**不出现**「平台实勘」。

- [ ] **Step 7: 提交**

```bash
git add src/commission/gui/steps/step_roles.py src/commission/cli.py tests/test_gui.py
git commit -m "fix: hide platform role from role selection in GUI and CLI"
```

---

## Task 4: 展示侧 — 平台角色标注「平台收取」

**Files:**
- Modify: `src/commission/gui/steps/step_result.py`
- Modify: `src/commission/cli.py`
- Test: `tests/test_gui.py`

- [ ] **Step 1: 新增展示标注测试（写失败测试）**

在 `tests/test_gui.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 跑测试验证失败**

Run: `uv run pytest tests/test_gui.py::test_buyer_result_marks_platform_role -v`
Expected: FAIL — 当前标注为两分支，平台实勘被标成「（它店）」。

- [ ] **Step 3: 修改 `step_result.py` 标注为三分支**

a) import 加入 `PLATFORM_ROLES`：

```python
from commission.config import PAYMENT_RATES, PLATFORM_ROLES, RENTAL, RENTAL_ROLES, SALE_ROLES
```

b) `_format_buyer` 中 Step 2 的角色遍历改为：

```python
        for side, detail in [("业主", r.owner_detail), ("客户", r.customer_detail)]:
            lines.append(f"  {side}方：")
            for role, share in detail.role_shares.items():
                if role in PLATFORM_ROLES:
                    mark = "（平台收取）"
                elif role in r.my_roles:
                    mark = "（本店）"
                else:
                    mark = "（它店）"
                lines.append(f"   {role} {f(share)}{mark}")
```

- [ ] **Step 4: 修改 `cli.py` 标注为三分支**

`_show_buyer_result` 中 Step 2 的角色遍历改为：

```python
        for role, share in detail.role_shares.items():
            if role in PLATFORM_ROLES:
                owner_mark = "（平台收取）"
            elif role in r.my_roles:
                owner_mark = "（本店）"
            else:
                owner_mark = "（它店）"
            print(f"      {role}  {_fmt_money(share)}{owner_mark}")
```

（`cli.py` 已在 Task 3 引入 `PLATFORM_ROLES` import，无需重复添加。）

- [ ] **Step 5: 跑全量测试验证通过**

Run: `uv run pytest -q`
Expected: PASS（32 项全过）。

- [ ] **Step 6: ruff 最终检查**

Run: `uvx ruff check --select F401 src/ tests/`
Expected: `All checks passed!`

- [ ] **Step 7: 提交**

```bash
git add src/commission/gui/steps/step_result.py src/commission/cli.py tests/test_gui.py
git commit -m "feat: mark platform role as 平台收取 in result display"
```

---

## 收尾（计划之外，执行完成后确认）

- 文档同步：`README.md` 与 `cw-project.md`/`handoff.md` 中买卖角色表与数值若引用旧值，按需更新（可作为后续小任务）。
- 全量验证：`uv run pytest -q`（应 32 passed）、`uvx ruff check --select F401 src/ tests/`（应 0）、`uv run commission` 与 `uv run commission-gui` 手动各跑一次买卖成交人场景。
