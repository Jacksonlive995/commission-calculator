# Handoff 文档 — 佣金计算器 v0.2.0

> 最后更新：2026-05-31

## 项目概述

房产中介佣金计算工具（CLI + GUI）。业务场景：成交一套房源后，需要计算平台分账和业务员应发佣金。计算涉及6步流程，且角色组合多变，手动计算易出错。

## 已完成功能

### 核心计算（calculator.py）

纯函数，无IO，所有结果四舍五入到分。

**成交人视角** `calc_buyer_commission()`
- Step 1: 理房通平台费（按支付方式费率）
- Step 2: 角色业绩拆分（按角色占比分配给各门店）
- Step 3: 成交人实收佣金 = 总额 - 理房通费 - 其他门店角色份额
- Step 4: 德佑平台服务费 = 实收 × 8%
- Step 5: 进店实收业绩 = 实收 - 德佑费
- Step 6: 业务员应发佣金 = 进店 × 50%

**房源方视角** `calc_seller_commission()`
- 我方份额 = 应收佣金 × 我方角色占比之和
- 德佑费、进店业绩、业务员佣金同上

**多业务员拆分** `calc_agent_shares()`
- 两个视角都支持通过 `agent_roles` 参数指定 角色→业务员姓名 映射
- 每人按角色占比从总份额中分配，再各自扣8%德佑费和50%提成
- 成交人视角中，"客源成交人"角色自动分配给名为"成交人"的业务员
- 不传 `agent_roles` 时向后兼容，`agent_shares` 只有一条总记录

### 交互式CLI（cli.py）

数字快捷选择支付方式，y/n 选择角色归属，支持"全部属于本店"快捷选项，支持按业务员拆分佣金并逐个输入姓名。

### 图形界面GUI（gui/）

PySide6 实现的向导式桌面应用，5步导航：① 房源类型 → ② 支付信息 → ③ 角色归属 → ④ 拆分设置 → ⑤ 结果。支持实时平台费预览、一键复制结果。CLI入口和GUI入口独立，calculator.py 未做任何修改。

文件结构：
- `gui/app.py` — GUI入口，创建 QApplication 和主窗口
- `gui/wizard.py` — 向导主窗口，QStackedWidget 步骤导航，上一步/下一步按钮控制
- `gui/steps/step_type.py` — 房源类型（租赁/买卖）+ 计算视角（成交人/房源方）
- `gui/steps/step_payment.py` — 支付金额输入 + 支付方式下拉 + 实时费率预览；房源方视角只显示一个总额输入
- `gui/steps/step_roles.py` — 角色复选框列表 + 全部本店/全部它店快捷按钮
- `gui/steps/step_split.py` — 拆分开关 + 同一人/逐个指定 + 姓名输入
- `gui/steps/step_result.py` — 格式化结果展示（与CLI输出一致）+ 复制按钮

### 配置常量（config.py）

租赁4角色、买卖6角色（含平台实勘3%，由 PLATFORM_ROLES 标记为平台角色）、8种支付费率、8%德佑费、50%提成。

## 关键设计决策

1. **平台实勘3%作为独立平台角色参与分账**（2026-05-31 修正了早期"不参与分账"的实现）：买卖3%平台实勘费建模为 `SALE_ROLES` 中的「平台实勘」角色，用 `PLATFORM_ROLES` 标记。它作为「非我方角色」自动从成交人份额扣除，使成交人份额回到业务规则的 60%（此前未扣除，成交人多拿 3%、实拿 63%）。该角色永不属门店：GUI/CLI 不可勾选、不参与业务员拆分，calculator 入口有防御兜底。详见 `docs/superpowers/specs/2026-05-30-sale-platform-viewing-role-design.md`。
2. **文档笔误修正**：cw-project.md 中有两处算术笔误——租赁示例钥匙人5%被算成10%，买卖示例 `10000-30-1000-1500-200-500-500` 文档写6570但实际等于6270。代码按正确数学计算实现。
3. **租赁维护人10%**：用户确认租赁维护人业绩占比为10%（非文档中写的5%），成交人占60%。
4. **agent_shares 接收未扣德佑费的份额**：`calc_agent_shares` 的 `total_share` 参数是未扣8%德佑费的份额（成交人视角为 `total_received`，房源方视角为 `my_share`），这样每人在拆分时各自独立扣8%和50%，避免双重扣费或不公平分配。
5. **不传 agent_roles 时**：`agent_shares` 接收的是 `store_income`（已扣8%），因为此时只有一条总记录，不需要再扣德佑费，只需乘50%。

## 测试覆盖

34个测试用例，全部通过：

| 测试类/文件 | 用例数 | 覆盖场景 |
|--------|--------|----------|
| TestPaymentFee | 2 | 理房通费率计算 |
| TestBuyerCommissionRental | 7 | 租赁成交人，所有角色属于它店 |
| TestBuyerCommissionSale | 7 | 买卖成交人，含平台实勘角色，成交人占60% |
| TestBuyerCommissionRentalAllRoles | 2 | 租赁成交人兼任全部角色 |
| TestBuyerCommissionRentalPartialRoles | 2 | 租赁成交人兼任部分角色 |
| TestSellerCommission | 2 | 房源方单角色/多角色 |
| TestSellerAgentShares | 2 | 房源方2人/3人拆分 |
| TestBuyerAgentShares | 2 | 成交人角色拆分 + 向后兼容 |
| TestPlatformViewingRole | 3 | 平台角色边界：误传my_roles/不分配业务员/房源方 |
| test_gui.py | 5 | GUI边框闭合、平台角色勾选排除、展示标注「平台收取」、setup前get_state |

## 已知限制 / 未来可做

- CLI 不支持批量计算（一次只算一笔）
- 没有持久化/历史记录功能
- 角色和费率硬编码在 config.py 中，修改需改代码
- GUI 界面缺少输入验证的视觉反馈（如红框提示）

## 运行命令

```bash
uv run commission       # 启动交互式CLI
uv run commission-gui   # 启动图形界面
uv run pytest -v        # 运行测试
```
