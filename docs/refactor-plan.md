# 佣金计算器结构化整理计划

> 本计划用于指导当前项目从“功能堆叠完成”进入“结构清晰可维护”阶段。当前有效业务规则以 `docs/business-rules.md` 为准。

## 目标

- 统一业务规则来源。
- 消除 CLI/GUI 结果格式化重复。
- 拆清飞书写入和记录转换边界。
- 移除 `config.py` 的 `.env` 加载副作用。
- 在不改变计算结果的前提下，逐步降低维护成本。

## 阶段 1：文档先行

### 1.1 当前有效业务规则

文件：`docs/business-rules.md`

内容：

- 当前角色比例
- 平台实勘规则
- 理房通费率
- 德佑 8% 规则
- 成交人视角计算流程
- 房源方视角计算流程
- 多业务员拆分规则
- 历史修正记录

验证：

```bash
uv run pytest tests/test_calculator.py -q
```

### 1.2 架构备注

文件：`docs/architecture-notes.md`

内容：

- 每个模块的职责边界
- 当前耦合点
- 后续拆分顺序
- 明确不动项

验证：

```bash
uv run pytest -q
```

## 阶段 2：统一展示层

新增：`src/commission/formatter.py`

目标：

- 把 CLI 的结果展示逻辑和 GUI 的结果格式化逻辑合并。
- CLI 只负责 `print()`。
- GUI 只负责 `setPlainText()`。

需要修改：

- `src/commission/cli.py`
- `src/commission/gui/steps/step_result.py`
- `tests/test_gui.py`

验证：

```bash
uv run pytest tests/test_calculator.py tests/test_gui.py -q
```

## 阶段 3：拆出记录转换层

新增：`src/commission/records.py`

目标：

- `CommissionRecord` 从 `feishu.py` 移出。
- `extract_records()` 从 `feishu.py` 移出。
- `feishu.py` 只接受记录并写入飞书。

需要修改：

- `src/commission/feishu.py`
- `src/commission/cli.py`
- `src/commission/gui/steps/step_result.py`
- `tests/test_feishu.py`

验证：

```bash
uv run pytest tests/test_feishu.py -q
uv run pytest -q
```

## 阶段 4：清理配置副作用

新增：`src/commission/settings.py` 或 `src/commission/env.py`

目标：

- `config.py` 只保留业务常量。
- `.env` 查找和飞书凭证读取移动到独立配置模块。
- 导入业务常量时不再隐式读取文件。

需要修改：

- `src/commission/config.py`
- `src/commission/feishu.py`
- `tests/test_feishu.py`

验证：

```bash
uv run pytest tests/test_feishu.py -q
uv run pytest -q
```

## 阶段 5：整理复杂拆分逻辑

目标：

- 保持现有计算结果不变。
- 先补充拆分合计测试。
- 再考虑把成交人/房源方拆分逻辑拆成更清楚的内部函数。

需要修改：

- `src/commission/calculator.py`
- `tests/test_calculator.py`

验证：

```bash
uv run pytest tests/test_calculator.py -q
```

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
