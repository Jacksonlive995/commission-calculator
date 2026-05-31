# 佣金计算器

房产中介佣金计算工具（CLI + 图形界面）。输入房源信息、支付金额和角色归属，自动完成6步分账计算并输出每笔明细，支持一键写入飞书多维表格。

## 功能

- 两种房源类型：租赁 / 买卖
- 两种计算视角：成交人（我店成交它店房源）/ 房源方（它店成交我店房源）
- 6步计算流程：理房通平台费 → 角色业绩拆分 → 实收佣金 → 德佑平台服务费 → 进店实收 → 业务员应发
- 多业务员拆分：按角色占我方份额的比例分配进店业绩，8%德佑费只扣一次
- 买卖房源3%平台实勘费作为独立平台角色：从成交人份额扣除、永不属门店、不可勾选/不参与业务员拆分
- 成交人兼任房源方角色时自动调整占比
- 8种支付方式的快捷选择
- PySide6 图形界面（向导式5步导航，实时费率预览，一键复制结果）
- 飞书多维表格集成：计算结果按业务员分表写入，每人成交方/客源方各一页

## 业务规则

### 角色占比

| 角色 | 租赁 | 买卖 |
|------|------|------|
| 录入人 | 10% | 10% |
| 维护人 | 10% | 15% |
| 实勘人 | 10% | 2% |
| 钥匙人 | 5% | 5% |
| 证件人 | — | 5% |
| 平台实勘 | — | 3%（平台角色：从成交人份额扣除，不可由门店持有） |
| 客源成交人 | 60% | 60% |

> 成交人占比 = 100% - 其他角色占比之和。当部分角色由成交人兼任时，成交人占比自动增大。

### 支付通道费（理房通）

| 支付方式 | 费率 |
|----------|------|
| 微信小程序 | 0.65% |
| 微信APP | 0.65% |
| 微信扫码 | 0.3% |
| 支付宝APP | 0.3% |
| 支付宝扫码 | 0.3% |
| 快捷支付 | 0.4% |
| 银联线上支付 | 0.55% |
| 京东白条 | 0.3% |

### 提成规则

- 德佑平台服务费：实收佣金 × 8%（只扣一次，拆分时不再扣除）
- 业务员提成：进店实收 × 50%

## 安装

```bash
uv sync
```

## 使用

### 命令行

```bash
uv run commission
```

### 图形界面

```bash
uv run commission-gui
```

交互流程（CLI / GUI 通用）：
1. 选择房源类型（租赁/买卖）
2. 选择计算视角（成交人/房源方）
3. 输入支付金额和方式（数字快捷选择）
4. 选择角色归属（全部属于本店 / 逐个选择 / 全部不属于本店）
5. 选择是否按业务员拆分佣金，为每个角色指定业务员姓名
6. 输出完整6步计算明细 + 各业务员拆分明细
7. 选择是否写入飞书多维表格（CLI 询问 / GUI 按钮）

### 飞书多维表格

1. 复制 `.env.example` 为 `.env`，填入飞书开放平台的 App ID 和 App Secret
2. 首次写入时自动创建多维表格和数据表，后续写入复用
3. 每个业务员两个数据表：`姓名_成交方` 和 `姓名_客源方`
4. 每笔佣金写入一条记录，字段包含：日期、房源类型、角色、角色占比、佣金总额、我方份额、德佑费、进店业绩、应发佣金

### 打包为 Windows 可执行文件

```bash
uv run pyinstaller --onefile --windowed --name "佣金计算器" --noconfirm \
  --hidden-import commission --hidden-import commission.config \
  --hidden-import commission.calculator --hidden-import commission.feishu \
  --hidden-import commission.gui --hidden-import commission.gui.app \
  --hidden-import commission.gui.wizard \
  --hidden-import commission.gui.steps.step_type \
  --hidden-import commission.gui.steps.step_payment \
  --hidden-import commission.gui.steps.step_roles \
  --hidden-import commission.gui.steps.step_split \
  --hidden-import commission.gui.steps.step_result \
  src/commission/gui/launch.py
```

生成的 `dist/佣金计算器.exe` 可直接双击运行，无需安装 Python。`.env` 文件需与 exe 放在同一目录。

## 开发

```bash
uv run pytest # 运行测试（42个用例）
uv run pytest -v # 详细输出
uv run python -m commission # CLI入口
uv run commission-gui # GUI入口
```

## 项目结构

```
cw-project/
├── pyproject.toml # 项目配置
├── cw-project.md # 业务需求文档
├── src/commission/
│   ├── __init__.py
│   ├── config.py # 费率、角色比例等常量
│   ├── calculator.py # 纯计算逻辑（无IO）
│   ├── feishu.py # 飞书多维表格 API 封装
│   ├── cli.py # 交互式命令行入口
│   └── gui/ # PySide6 图形界面
│       ├── app.py # GUI入口
│       ├── wizard.py # 向导主窗口
│       └── steps/ # 各步骤页面
│           ├── step_type.py # 房源类型+视角
│           ├── step_payment.py # 支付信息
│           ├── step_roles.py # 角色归属
│           ├── step_split.py # 拆分设置
│           └── step_result.py # 结果展示
└── tests/
    ├── __init__.py
    ├── test_calculator.py # 计算逻辑单元测试
├── test_feishu.py # 飞书模块单元测试
    └── test_gui.py # GUI 展示/交互单元测试
```
