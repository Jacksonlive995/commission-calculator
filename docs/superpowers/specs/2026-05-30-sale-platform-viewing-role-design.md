# 设计文档：买卖「平台实勘 3%」改为独立角色

- **日期**：2026-05-30
- **状态**：待实现
- **主题**：把买卖房源被贝壳平台分走的 3% 平台实勘费，从「计算但不扣除」修正为一个独立角色，使成交人份额回到业务规则的 60%。

---

## 1. 背景与问题

买卖房源的佣金按角色占比分账，业务规则规定的占比为：

| 角色 | 占比 | 归属 |
|------|------|------|
| 录入人 | 10% | 门店 |
| 维护人 | 15% | 门店 |
| 实勘人 | 2% | 门店 |
| 钥匙人 | 5% | 门店 |
| 证件人 | 5% | 门店 |
| **平台实勘** | **3%** | **平台（VR 拍摄 / 摄影师，永不属门店）** |
| 客源成交人 | 60% | 门店 |

合计 100%。

**当前实现的缺陷**：`config.py` 用独立常量 `SALE_PLATFORM_VIEWING_RATE = 0.03` 表示这 3%，`calculator.py` 仅把它算成 `PaymentDetail.platform_viewing_fee` 字段用于展示，**从未从成交人份额中扣除**。结果：

- 成交人份额公式 `总额 − 通道费 − 非我方角色(37%)` 漏掉了这 3%，成交人实际拿到总额的 **63%** 而非 60%。
- 以「业主微信扫码 10000 + 客户微信扫码 10000、全部角色属它店」为例，成交人到手被算成 **5768.40**，比正确值 **5492.40** 多约 276 元。

注：`cw-project.md` 原始示例的 Step 3 公式本身也没有减这 3%（且有把 6270 误写成 6570 的算术笔误），代码忠实继承了这一不自洽。本设计修正它。

**不受影响的部分**：

- **租赁房源**：无平台角色，成交人占 65%，逻辑完全不变。
- **房源方视角**（它店成交我店房源）：只按「我方持有角色的占比」累加，平台 3% 本就不归我店，天然不受影响。

因此本次修正只触及**买卖 + 成交人视角**的份额计算，以及承载平台角色的输入/展示边界。

---

## 2. 目标

1. 买卖成交人份额修正为总额的 60%（3% 归平台）。
2. 用「角色」统一建模这 3%，移除游离在角色体系外的独立常量与字段。
3. 保证「平台实勘」永远不会被当作门店角色（不可勾选、不参与业务员拆分、不计入房源方占比），且这一约束有测试锁定。

## 3. 非目标（范围外）

- 不改租赁逻辑、不改房源方视角计算。
- 不改 8% 德佑平台服务费、50% 提成、支付通道费等其它规则。
- 不重构 GUI 向导结构、不新增持久化/批量计算等已知限制项。

---

## 4. 选定方案：新增「平台实勘」角色 + `PLATFORM_ROLES` 标记

### 关键洞察

把「平台实勘」加进 `SALE_ROLES` 后，它天然是一个「永远不属于我方」的角色，于是**核心计算公式无需特判**：

- 成交人份额 `总额 − 通道费 − 非我方角色`：平台实勘属「非我方」，自动被减去 → 成交人正好 60%。
- 业务员拆分 `calc_agent_shares`：只分配 `my_roles` 内的角色，平台实勘不在其中，自动不参与。
- 房源方占比 `calc_seller_commission`：只累加 `my_roles` 占比，平台实勘自动不计入。

特判因此集中在两个**边界**，且都以单一常量 `PLATFORM_ROLES` 作为事实来源：

- **输入侧**：不让用户把平台实勘选成自己的角色。
- **展示侧**：把平台角色标注为「（平台收取）」而非「（它店）」。

外加一道**入口防御**：`calculator.py` 在入口处剔除 `my_roles` 中的平台角色，确保即使有调用方绕过 UI 传入平台角色，计算依然正确。

---

## 5. 详细改动（按文件）

### 5.1 `src/commission/config.py`

```python
SALE_ROLES: dict[str, float] = {
    "录入人": 0.10,
    "维护人": 0.15,
    "实勘人": 0.02,
    "平台实勘": 0.03,   # 新增：平台收取（VR 拍摄），永不属门店
    "钥匙人": 0.05,
    "证件人": 0.05,
}   # 合计 40%

# 新增：平台角色集合（永不属门店、不可勾选、不参与拆分）
PLATFORM_ROLES: frozenset[str] = frozenset({"平台实勘"})

# 删除：SALE_PLATFORM_VIEWING_RATE（3% 已并入 SALE_ROLES）
```

`RENTAL_ROLES` 不变（租赁无平台角色）。

### 5.2 `src/commission/calculator.py`

- **import**：移除 `SALE_PLATFORM_VIEWING_RATE`，新增 `PLATFORM_ROLES`。
- **`PaymentDetail`**：删除字段 `platform_viewing_fee`（信息改由 `role_shares["平台实勘"]` 承载）。
- **`calc_buyer_commission`**：删除以下整段（不再需要单独计算平台费）——

  ```python
  # 平台实勘费（仅买卖），由平台直接收取，不从成交人份额中扣除
  if property_type == SALE:
      detail.platform_viewing_fee = round(amount * SALE_PLATFORM_VIEWING_RATE, 2)
  ```

  保留的份额循环天然把「平台实勘」计入 `role_shares` 且计入 `other_store_shares`（因其不在 `my_roles`），成交人份额自动变为 60%。

- **入口防御**（`calc_buyer_commission` 与 `calc_seller_commission` 开头各一行）：

  ```python
  my_roles = [r for r in my_roles if r not in PLATFORM_ROLES]
  ```

  核心公式不变，仅在入口剔除平台角色，保证误传也安全。

### 5.3 输入侧（防止平台实勘进入 `my_roles`）

- **`src/commission/gui/steps/step_roles.py`**：构建角色勾选框时跳过平台角色——
  ```python
  for role, rate in roles.items():
      if role in PLATFORM_ROLES:
          continue
      ...
  ```
- **`src/commission/cli.py`**：构建 `role_names` 时过滤平台角色——
  ```python
  role_names = [r for r in (RENTAL_ROLES if ... else SALE_ROLES) if r not in PLATFORM_ROLES]
  ```
  「全部属于本店 / 全部不属于本店 / 逐个选择」三个分支都基于过滤后的 `role_names`，故均安全。

### 5.4 展示侧（标注平台角色）

- **`src/commission/cli.py` `_show_buyer_result`** 与 **`src/commission/gui/steps/step_result.py` `_format_buyer`**：Step 2 逐角色展示的归属标注改为三分支——
  ```python
  if role in PLATFORM_ROLES:
      mark = "（平台收取）"
  elif role in my_roles:
      mark = "（本店）"
  else:
      mark = "（它店）"
  ```
- Step 3 的「成交人实收」展示中，减项 `other`（非我方角色之和）现在自然包含平台实勘 300，即 `10000 − 30 − 4000 = 5970`。这是预期行为，无需额外处理。
- 原先单独打印 `platform_viewing_fee` 的展示行删除（平台实勘已作为普通角色出现在 Step 2 列表中）。

---

## 6. 数值影响

以「买卖、业主微信扫码 10000、客户微信扫码 10000、全部角色属它店」为基准：

| 字段 | 修正前 | 修正后 |
|------|--------|--------|
| 角色拆分 | 录入1000/维护1500/实勘200/钥匙500/证件500 | 同前，**新增 平台实勘 300** |
| 非我方角色合计/笔 | 3700 | 4000 |
| 成交人实收/笔 `buyer_received` | 6270 | **5970**（= 10000×60% − 30 通道费） |
| 实收合计 `total_received` | 12540 | **11940** |
| 德佑服务费 `beike_fee` | 1003.20 | **955.20** |
| 进店实收 `store_income` | 11536.80 | **10984.80** |
| 业务员应发 `agent_commission` | 5768.40 | **5492.40** |

租赁、房源方视角数值不变。

---

## 7. 测试计划

遵循 TDD：先改/加测试看红，再改实现转绿。

1. **更新 `tests/test_calculator.py::TestBuyerCommissionSale`**（先红）：
   - `test_buyer_received`：6270 → 5970，total 12540 → 11940
   - `test_beike_fee`：1003.2 → 955.2
   - `test_store_income`：11536.8 → 10984.8
   - `test_agent_commission`：5768.4 → 5492.4
   - `test_owner_role_shares`：新增断言 `role_shares["平台实勘"] == 300`
   - `test_platform_viewing_fee`：改为断言 `role_shares["平台实勘"] == 300`（不再用已删除的 `platform_viewing_fee` 字段）
2. **新增回归测试 `TestPlatformViewingRole`**：
   - 误传 `my_roles=["平台实勘"]` 时，成交人份额仍为 5970/笔（入口防御生效，3% 不被算给成交人）。
   - 误传 `my_roles=["平台实勘"]` + `agent_roles={"平台实勘": "张三"}` 时，`agent_shares` 不包含张三（平台角色不参与拆分）。
3. **新增 GUI 回归测试**（`tests/test_gui.py`）：买卖时 `StepRoles.setup` 后的勾选框不含「平台实勘」。
4. 全量测试通过；`ruff --select F401` 保持为 0（删除 `SALE_PLATFORM_VIEWING_RATE` 后检查无遗留引用）。

---

## 8. 风险与对策

| 风险 | 对策 |
|------|------|
| 某处漏掉「排除平台角色」，导致 3% 被误算/误分 | 用单一常量 `PLATFORM_ROLES` 做所有判断；入口防御兜底；回归测试锁定 |
| 删除 `SALE_PLATFORM_VIEWING_RATE` 后有遗留引用 | 全量搜索 + `ruff F401` + 全量测试 |
| 展示文案误把平台角色标成「它店」 | 展示侧三分支显式判断 + 人工核对一次实际输出 |

---

## 9. 验收标准

- 买卖成交人到手为修正后的数值（基准案例 5492.40）。
- 平台实勘在 CLI/GUI 角色选择中不可见、不可选。
- 即便 `my_roles` 含平台角色，计算结果不变。
- 全量测试通过，F401 为 0。
- 租赁、房源方视角行为与数值不变。
