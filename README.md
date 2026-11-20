# 佣金计算器（Commission Calculator）

项目目录：`commission-calculator`。GitHub 仓库：https://github.com/Jacksonlive995/commission-calculator。

房产中介佣金计算工具（CLI + 图形界面）。输入房源信息、支付金额和角色归属，自动完成 6 步分账计算并输出每笔明细，支持一键写入飞书多维表格。

> 当前有效业务规则以 `docs/business-rules.md` 为准。`cw-project.md` 保留原始需求记录和历史算例，其中部分比例与算术已在后续确认中修正。

## 功能

- 两种房源类型：租赁 / 买卖
- 两种计算视角：成交人（我店成交它店房源）/ 房源方（它店成交我店房源）
- 6 步计算流程：理房通平台费 → 角色业绩拆分 → 实收佣金 → 德佑平台服务费 → 进店实收 → 业务员应发
- 多业务员拆分：按角色占我方份额的比例分配进店业绩，8% 德佑费只扣一次
- 买卖房源 3% 平台实勘费作为独立平台角色：从成交人份额扣除、永不属门店、不可勾选/不参与业务员拆分
- 成交人兼任房源方角色时自动调整占比
- 8 种支付方式的快捷选择
- PySide6 图形界面（向导式 5 步导航，统一视觉样式，实时费率预览，一键复制结果）
- 飞书多维表格集成：计算结果按业务员分表写入，每人成交方/客源方各一页

## 业务规则

核心业务规则请查看：`docs/business-rules.md`

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

### 首次使用快速上手

1. 安装依赖：`uv sync`
2. 配置飞书：复制 `.env.example` 为 `.env`，填写 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`
3. 启动程序：`uv run commission` 或 `uv run commission-gui`
4. 按流程录入房源类型、视角、支付金额、角色归属和业务员姓名
5. 查看 6 步结果；需要时选择写入飞书

### 交互流程

CLI / GUI 通用流程：

1. 选择房源类型（租赁 / 买卖）
2. 选择计算视角（成交人 / 房源方）
3. 输入支付金额和方式（数字快捷选择）
4. 选择角色归属（全部属于本店 / 逐个选择 / 全部不属于本店）
5. 选择是否按业务员拆分佣金，为每个角色指定业务员姓名
6. 输出完整 6 步计算明细 + 各业务员拆分明细
7. 选择是否写入飞书多维表格（CLI 询问 / GUI 按钮）

### 飞书多维表格

1. 复制 `.env.example` 为 `.env`，填入飞书开放平台的 App ID 和 App Secret
2. 首次写入时自动创建多维表格和数据表，后续写入复用
3. 每个业务员两个数据表：`姓名_成交方` 和 `姓名_客源方`
4. 每笔佣金写入一条记录，字段包含：日期、房源类型、角色、角色占比、佣金总额、我方份额、德佑费、进店业绩、应发佣金

### 打包为 Windows 可执行文件

在 Windows 上执行：

```bash
uv sync --locked --group dev
uv run --frozen pyinstaller --noconfirm --clean "佣金计算器.spec"
```

生成的 `dist/佣金计算器.exe` 可直接双击运行，无需安装 Python。需要写入飞书时，将配置好的 `.env` 文件放在 exe 同目录。图标与打包配置位于 `assets/app.ico` 和 `佣金计算器.spec`。

### 使用 GitHub Actions 自动编译

工作流配置位于 `.github/workflows/build.yml`。推送到 `main`、向 `main` 提交 Pull Request，或在 GitHub 的 **Actions → Build → Run workflow** 手动触发，都会在 Windows x64 上执行：

1. 安装 Python 3.12 和锁定的开发依赖
2. 运行全部测试（Qt 使用无显示器模式）
3. 构建 Python 源码包和 wheel，再使用 `佣金计算器.spec` 打包 Windows 程序
4. 上传 `commission-calculator-windows-x64` 构建产物，保留 30 天

在成功的运行页面下方 **Artifacts** 下载并解压 `commission-calculator-windows-x64`，即可双击 `佣金计算器.exe`。需要写入飞书时，将同目录的 `.env.example` 复制为 `.env`，填写自己的 App ID 和 App Secret。

编译无需配置飞书凭证；构建产物只包含配置示例。

### 自动发布到 GitHub Releases

推送 `v` 开头的版本标签（例如 `v0.2.0`）后，Actions 会校验标签与 `pyproject.toml` 的版本一致，运行测试并打包 Windows 程序。构建成功后，自动创建对应的 [GitHub Release](https://github.com/Jacksonlive995/commission-calculator/releases)，上传以下附件：

- `commission-calculator-windows-x64.exe`：可直接运行的 Windows x64 程序
- `env.example`：飞书配置示例，使用时复制为 EXE 同目录的 `.env`
- `commission-calculator-v0.2.0-windows-x64.zip`：包含 `佣金计算器.exe` 和 `.env.example`，文件名随版本变化

Release 附件会长期保留。普通推送到 `main` 会运行测试和编译；发布正式版本时，推送对应的版本标签：

```bash
# 项目版本为 0.2.0，且代码已提交并推送到 main 时
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

每个版本使用一个新标签。发布后续版本时，先更新 `pyproject.toml` 的版本号，执行 `uv lock` 并提交、推送版本修改，再推送对应标签（例如 `v0.2.1`）。发布使用 GitHub 自动提供的令牌，无需额外配置个人访问令牌。

## 最终使用说明

如果你只想“先跑起来”，按下面做就够了：

- **本地运行**：先执行 `uv sync`
- **命令行**：执行 `uv run commission`
- **图形界面**：执行 `uv run commission-gui`
- **飞书写入**：先准备 `.env`，再在结果页点击写入
- **打包后运行**：双击 exe；需要写入飞书时再把 `.env` 放到 exe 同目录

常见问题：

- **飞书写入失败**：先检查 `.env` 里是否配置了 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`
- **打包后飞书写入失败**：确认 exe 同目录的 `.env` 已填写正确的飞书凭证
- **结果和文档不一致**：以 `docs/business-rules.md` 为准，`cw-project.md` 只保留原始记录

## 开发

```bash
uv run pytest tests # 运行项目测试
uv run pytest -v # 详细输出
uv run commission # CLI 入口
uv run commission-gui # GUI 入口
```

## 项目结构

```
commission-calculator/
├── .github/workflows/build.yml # GitHub Actions 测试、Windows 打包与 Release 发布
├── 佣金计算器.spec # PyInstaller 打包配置
├── assets/app.ico # 应用图标
├── pyproject.toml # 项目配置
├── cw-project.md # 原始业务需求文档
├── docs/
│   ├── business-rules.md # 当前有效业务规则
│   ├── architecture-notes.md # 模块职责与重构备注
│   └── refactor-plan.md # 后续结构化整理计划
├── src/commission/
│   ├── __init__.py
│   ├── config.py # 费率、角色比例等业务常量
│   ├── settings.py # .env 与飞书运行配置
│   ├── calculator.py # 纯计算逻辑（无 IO）
│   ├── formatter.py # CLI/GUI 共用结果格式化
│   ├── records.py # 计算结果转外部记录
│   ├── feishu.py # 飞书多维表格 API 封装
│   ├── cli.py # 交互式命令行入口
│   └── gui/ # PySide6 图形界面
│       ├── launch.py # PyInstaller 打包入口
│       ├── app.py # GUI 入口
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
