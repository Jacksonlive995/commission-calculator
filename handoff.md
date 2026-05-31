# Handoff 文档 — 佣金计算器 v0.3.0

> 最后更新：2026-05-31
> 当前有效业务规则以 `docs/business-rules.md` 为准；`cw-project.md` 仅作为原始需求记录，保留了历史笔误和后续修正前的描述。

## 项目概述

房产中介佣金计算工具（CLI + GUI + 飞书多维表格）。业务场景：成交一套房源后，需要计算平台分账和业务员应发佣金。计算涉及6步流程，且角色组合多变，手动计算易出错。

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
- 8% 德佑费只扣一次（在总账 Step 4），拆分到具体业务员时不再扣除
- 成交人视角：先算各角色在 total_received 中的实际金额（房源方角色 = 总金额 × 角色占比；成交人角色 = total_received - 房源方角色份额合计），各自 ×0.92 得到进店份额，再按业务员分组汇总后 ×50%
- 房源方视角：按角色占我方份额的比例分配进店业绩（角色rate / 我方总rate），再 ×50%
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
- `gui/steps/step_result.py` — 格式化结果展示（与CLI输出一致）+ 复制按钮 + 写入飞书按钮

### 飞书多维表格集成（feishu.py）

计算完成后可将结果逐笔写入飞书多维表格，按业务员分表统计。

- **首次使用自动创建**：调用飞书 API 创建多维表格应用及数据表，`app_token` 保存到 `~/.commission/feishu_config.json`，后续复用
- **按业务员+视角分表**：每个业务员两个数据表（如 `张三_成交方`、`张三_客源方`），新业务员自动建表
- **数据表字段**：日期、房源类型（单选）、角色（文本）、角色占比（数字0.10=10%）、佣金总额、我方份额、德佑费、进店业绩、应发佣金
- **CLI**：计算完成后询问是否写入飞书
- **GUI**：结果页「写入飞书」按钮，点击后弹窗显示成功/失败
- **凭证配置**：从 `.env` 文件读取 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`，查找顺序：项目根目录 → exe同级目录 → 当前工作目录
- **认证**：tenant_access_token 带缓存（2小时有效期），注意认证接口的 token 在 JSON 顶层而非 `data` 字段
- **飞书应用权限**：需在飞书开放平台开通 `bitable:app` 和 `base:app:create` 权限，否则报 Access denied

### 配置常量（config.py）

租赁4角色、买卖6角色（含平台实勘3%，由 PLATFORM_ROLES 标记为平台角色）、8种支付费率、8%德佑费、50%提成、飞书API凭证（从 .env 读取）。

## 关键设计决策

1. **平台实勘3%作为独立平台角色参与分账**（2026-05-31 修正了早期"不参与分账"的实现）：买卖3%平台实勘费建模为 `SALE_ROLES` 中的「平台实勘」角色，用 `PLATFORM_ROLES` 标记。它作为「非我方角色」自动从成交人份额扣除，使成交人份额回到业务规则的 60%。该角色永不属门店：GUI/CLI 不可勾选、不参与业务员拆分，calculator 入口有防御兜底。
2. **文档笔误修正**：cw-project.md 中有两处算术笔误——租赁示例钥匙人5%被算成10%，买卖示例 `10000-30-1000-1500-200-500-500` 文档写6570但实际等于6270。代码按正确数学计算实现。
3. **租赁维护人10%**：用户确认租赁维护人业绩占比为10%（非文档中写的5%），成交人占60%。
4. **8%德佑费只扣一次**（2026-05-31 修正了双重扣除bug）：此前拆分到具体业务员时，每人各自又扣了一次8%，导致总扣除额远超8%。修正后：总账层面扣一次8%得到 store_income，拆分时各人按实际份额直接 ×50%，不再扣8%。
5. **拆分按我方内部比例分配**（2026-05-31 修正）：房源方视角中，角色rate是相对总金额的占比（如录入人10%），拆分时需转换为相对我方份额的占比（10%/20%=50%），否则同一业务员持有全部角色时只分到角色rate之和比例而非100%。成交人视角中，用各角色在 total_received 中的实际金额分配，避免角色占比之和超过100%导致分配总额超过 store_income。
6. **飞书多维表格按业务员分表**（2026-05-31）：不按房源类型分表，而按业务员+视角分表（如`张三_成交方`、`张三_客源方`），便于个人业绩统计。首次使用自动创建整个表格结构，后续只创建新业务员的数据表。
7. **飞书API踩坑记录**（2026-05-31）：(a) 认证接口 `tenant_access_token` 在 JSON 顶层而非 `data` 里；(b) 创建数据表时不支持 `type=14`（percent），用 `type=2`（number）代替，写入时传 0.10 表示 10%；(c) date 字段不能带 property 参数；(d) 分页判断需用 `has_more` 而非 `page_token` 是否为空（最后一页 page_token 仍非空但 has_more=false）。

## 测试覆盖

42个测试用例，全部通过：

| 测试类/文件 | 用例数 | 覆盖场景 |
|--------|--------|----------|
| TestPaymentFee | 2 | 理房通费率计算 |
| TestBuyerCommissionRental | 7 | 租赁成交人，所有角色属于它店 |
| TestBuyerCommissionSale | 7 | 买卖成交人，含平台实勘角色，成交人占60% |
| TestBuyerCommissionRentalAllRoles | 2 | 租赁成交人兼任全部角色 |
| TestBuyerCommissionRentalPartialRoles | 2 | 租赁成交人兼任部分角色 |
| TestSellerCommission | 2 | 房源方单角色/多角色 |
| TestSellerAgentShares | 2 | 房源方2人/3人拆分（按我方内部比例分配） |
| TestBuyerAgentShares | 2 | 成交人角色拆分 + 向后兼容 |
| TestPlatformViewingRole | 3 | 平台角色边界：误传my_roles/不分配业务员/房源方 |
| test_gui.py | 5 | GUI边框闭合、平台角色勾选排除、展示标注「平台收取」、setup前get_state |
| TestTableName | 2 | 飞书数据表命名规则 |
| TestExtractRecords | 3 | 从计算结果提取佣金记录（成交人/房源方/无拆分） |
| TestWriteToFeishu | 3 | 首次写入创建表格/复用已有表格/API错误处理 |

## 打包

```bash
uv run pyinstaller --onefile --windowed --name "佣金计算器" --noconfirm   --hidden-import commission --hidden-import commission.config   --hidden-import commission.calculator --hidden-import commission.feishu   --hidden-import commission.gui --hidden-import commission.gui.app   --hidden-import commission.gui.wizard   --hidden-import commission.gui.steps.step_type   --hidden-import commission.gui.steps.step_payment   --hidden-import commission.gui.steps.step_roles   --hidden-import commission.gui.steps.step_split   --hidden-import commission.gui.steps.step_result   src/commission/gui/launch.py
```

生成 `dist/佣金计算器.exe`（约46MB，含PySide6运行时），Windows 10 可直接双击运行。
- `.env` 文件需与 `.exe` 放在同一目录
- `launch.py` 是 PyInstaller 入口（带错误捕获弹窗），不是正常的 `app.py`
- `--hidden-import` 必须显式列出所有子模块，否则 PyInstaller 不会打包

## 已知限制 / 未来可做

- CLI 不支持批量计算（一次只算一笔）
- 没有持久化/历史记录功能
- 角色和费率硬编码在 config.py 中，修改需改代码
- GUI 界面缺少输入验证的视觉反馈（如红框提示）
- .exe 双击没反应时需排查（可能缺少 .env 或 PyInstaller 打包遗漏模块）

## 运行命令

```bash
uv run commission # 启动交互式CLI
uv run commission-gui # 启动图形界面
uv run pytest -v # 运行测试
```
