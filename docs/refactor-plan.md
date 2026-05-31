# 佣金计算器结构化整理计划

> 本计划用于指导当前项目从“功能堆叠完成”进入“结构清晰可维护”阶段。当前有效业务规则以 `docs/business-rules.md` 为准。
>
> 状态：阶段 1～5 已完成，当前版本作为整理回顾与后续建议保留。

## 目标

- 统一业务规则来源。
- 消除 CLI/GUI 结果格式化重复。
- 拆清飞书写入和记录转换边界。
- 移除 `config.py` 的 `.env` 加载副作用。
- 在不改变计算结果的前提下，逐步降低维护成本。

## 已完成的阶段

### 阶段 1：文档先行

- `docs/business-rules.md` 已建立为当前有效业务规则的唯一来源。
- `docs/architecture-notes.md` 已记录模块职责边界、耦合点和不动项。
- `README.md`、`handoff.md`、`cw-project.md` 已补充引用和修正说明。

验证结果：`uv run pytest -q` 通过。

### 阶段 2：统一展示层

- 已新增 `src/commission/formatter.py`。
- CLI 和 GUI 已共用统一 formatter。
- 结果展示不再重复维护。

验证结果：`uv run pytest tests/test_calculator.py tests/test_gui.py -q` 通过。

### 阶段 3：拆出记录转换层

- 已新增 `src/commission/records.py`。
- `CommissionRecord` 与 `extract_records()` 已移出 `feishu.py`。
- `feishu.py` 现在只负责飞书写入与表管理。

验证结果：`uv run pytest tests/test_feishu.py -q`、`uv run pytest -q` 通过。

### 阶段 4：清理配置副作用

- 已新增 `src/commission/settings.py`。
- `config.py` 已只保留业务常量。
- `.env` 读取和飞书凭证读取已移出业务常量模块。

验证结果：`uv run pytest tests/test_feishu.py -q`、`uv run pytest -q` 通过。

### 阶段 5：整理复杂拆分逻辑

- 已补充拆分合计一致性测试。
- 已拆出成交人/房源方两个辅助入口。
- `calc_agent_shares()` 保留为兼容封装，结果未变。

验证结果：`uv run pytest tests/test_calculator.py -q`、`uv run pytest -q` 通过。

## 下一阶段建议

当前结构化整理已经完成，不建议继续沿着同一条线扩展重构。下一阶段更适合做的是“验收和收口”，例如：

- 再跑一次 CLI / GUI 典型流程，确认交互体验和展示文本没有回退。
- 检查 PyInstaller 打包入口和 hidden import 是否仍然完整。
- 整理 README 的使用说明，确保新用户能直接跑起来。
- 如果后面还有新需求，单独开新计划，不要继续塞进这份整理计划。

## 当前阶段不做

- 不重写 GUI。
- 不把业务规则做成可视化编辑。
- 不新增数据库或历史记录。
- 不扩展飞书表结构。
- 不改打包流程。
- 不调整已确认的业务算法。

## 每步完成标准

每一步都必须满足：

1. 对应测试通过。
2. 不改变已知算例结果。
3. 不扩大当前任务范围。
4. 文档与代码职责保持一致。
