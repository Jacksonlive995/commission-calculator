# GUI 美化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 PySide6 基础上做轻量级“大厂风”视觉优化，让 GUI 统一、克制、层次清晰，但不重写流程、不改计算逻辑、不引入复杂主题系统。

**Architecture:** 采用“统一样式 + 局部微调”的方式：先抽出一个集中的样式模块，统一窗口背景、卡片、按钮、输入框、步骤标题和结果页排版，再在各步骤页做最小布局调整。重点放在结果页和主窗口的视觉层次，保持现有交互不变，避免把美化变成重构。

**Tech Stack:** Python 3.12, PySide6, pytest, pathlib, QSS(Qt Style Sheet)

---

## Context

当前 GUI 的主要问题不是功能，而是视觉表达偏“脚本工具感”：

- 主窗口和步骤页基本是默认控件堆叠，层次感弱。
- 按钮、输入框、说明文字缺少统一风格。
- 结果页虽然功能完整，但更像纯文本输出，不像正式报表。
- 部分布局仍偏紧，留白、对齐和视觉重点不够。

本次美化只做视觉与排版提升，不做以下事情：

- 不改业务流程。
- 不改计算逻辑。
- 不改飞书写入逻辑。
- 不引入第三方 UI 框架。
- 不做暗色模式、动画或复杂主题系统。

---

## File map

### 统一样式层
- Create: `src/commission/gui/styles.py` — 集中管理 QSS、通用间距、颜色和控件样式。
- Modify: `src/commission/gui/wizard.py` — 应用全局样式，统一主窗口容器和步骤指示器。
- Modify: `src/commission/gui/app.py` — 在应用启动时加载统一样式。

### 步骤页视觉微调
- Modify: `src/commission/gui/steps/step_type.py` — 调整标题、单选按钮组和整体留白。
- Modify: `src/commission/gui/steps/step_payment.py` — 优化表单对齐、平台费预览、总额区域的视觉层级。
- Modify: `src/commission/gui/steps/step_roles.py` — 强化角色选择区域、快捷按钮和说明文字样式。
- Modify: `src/commission/gui/steps/step_split.py` — 优化拆分区域展开后的层次感和输入框排列。
- Modify: `src/commission/gui/steps/step_result.py` — 重做结果页布局，增强“报表感”和操作按钮层级。

### 测试层
- Modify: `tests/test_gui.py` — 增加样式和布局回归测试，确认视觉增强不破坏现有行为。

### 文档层
- Modify: `README.md` — 如有必要，补一句“GUI 已做统一视觉优化”，并保留运行方式。
- Modify: `handoff.md` — 记录 GUI 美化完成后当前界面定位。

---

## Task 1: 抽出统一 GUI 样式入口

**Files:**
- Create: `src/commission/gui/styles.py`
- Modify: `src/commission/gui/app.py`
- Modify: `src/commission/gui/wizard.py`

- [ ] **Step 1: 写样式使用约束测试**

新增一个轻量测试，确认 GUI 启动后能拿到统一样式入口，而不是每个页面各写一套样式。

```python
from commission.gui.styles import build_stylesheet


def test_gui_stylesheet_contains_core_tokens():
    css = build_stylesheet()
    assert "QMainWindow" in css
    assert "QPushButton" in css
    assert "QLineEdit" in css
    assert "QTextEdit" in css
```

- [ ] **Step 2: 运行测试确认当前缺少统一样式模块**

Run: `uv run pytest tests/test_gui.py -q`
Expected: 先因 `build_stylesheet` 未定义而失败，证明测试确实覆盖到新边界。

- [ ] **Step 3: 实现统一 QSS 生成函数**

在 `src/commission/gui/styles.py` 中新增：

```python
from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QMainWindow {
        background: #f5f7fb;
    }
    QWidget {
        color: #1f2937;
        font-size: 13px;
    }
    QLabel#PageTitle {
        font-size: 18px;
        font-weight: 600;
        color: #111827;
    }
    QLabel#PageSubtitle {
        color: #6b7280;
    }
    QFrame#Card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
    }
    QPushButton {
        min-height: 36px;
        border-radius: 8px;
        padding: 6px 14px;
        background: #ffffff;
        border: 1px solid #d1d5db;
    }
    QPushButton:hover {
        background: #f9fafb;
    }
    QPushButton#PrimaryButton {
        background: #2563eb;
        color: white;
        border: none;
    }
    QPushButton#PrimaryButton:hover {
        background: #1d4ed8;
    }
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {
        min-height: 34px;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 6px 10px;
        background: white;
    }
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
        border: 1px solid #2563eb;
    }
    """
```

- [ ] **Step 4: 让应用启动时一次性加载样式**

在 `src/commission/gui/app.py` 中创建 `QApplication` 后调用 `app.setStyleSheet(build_stylesheet())`。

- [ ] **Step 5: 跑测试确认样式入口稳定**

Run: `uv run pytest tests/test_gui.py -q`
Expected: 通过，且不会影响现有 GUI 逻辑。

---

## Task 2: 重塑主窗口和步骤页的视觉层次

**Files:**
- Modify: `src/commission/gui/wizard.py`
- Modify: `src/commission/gui/steps/step_type.py`
- Modify: `src/commission/gui/steps/step_payment.py`
- Modify: `src/commission/gui/steps/step_roles.py`
- Modify: `src/commission/gui/steps/step_split.py`

- [ ] **Step 1: 写主窗口布局回归测试**

确认主窗口仍然包含 5 个步骤页、导航按钮和步骤指示器。

```python
from commission.gui.wizard import CommissionWizard


def test_wizard_keeps_five_steps(qapp):
    wizard = CommissionWizard()
    assert wizard.stack.count() == 5
    assert wizard.btn_prev.text() == "上一步"
    assert wizard.btn_next.text() == "下一步"
```

- [ ] **Step 2: 运行测试确认当前视觉调整会触发回归失败**

Run: `uv run pytest tests/test_gui.py -q`
Expected: 如果新增了主窗口样式依赖但还没接入，会出现断言或样式缺失问题，确认测试真的约束到了窗口结构。

- [ ] **Step 3: 给主窗口增加“卡片式容器”与更清晰的步骤条**

在 `wizard.py` 中把主内容包进一个内容卡片，并把步骤指示器改为更像步骤条的样式。

```python
self.step_indicator.setObjectName("PageSubtitle")
self.step_indicator.setText("① 房源类型  →  ② 支付信息  →  ③ 角色归属  →  ④ 拆分设置  →  ⑤ 结果")
```

按钮区：

```python
self.btn_next.setObjectName("PrimaryButton")
```

- [ ] **Step 4: 统一各步骤页的顶部标题与留白**

在每个 step 页面增加一个统一的顶部标题区，例如：
- `StepType`："选择房源类型和计算视角"
- `StepPayment`："输入支付金额和平台费"
- `StepRoles`："选择本店持有的角色"
- `StepSplit`："设置业务员拆分方式"

每页统一使用较大的顶部留白、较小的说明文字和一个内容卡片。

- [ ] **Step 5: 让输入控件和快捷按钮更像正式工具**

- `StepPayment` 中把平台费预览区域做成浅灰提示块。
- `StepRoles` 中把“全部属于本店 / 全部不属于本店”按钮改成同宽主次按钮。
- `StepSplit` 中把“按业务员拆分佣金”作为更醒目的开关标题。

- [ ] **Step 6: 跑 GUI 回归测试确认结构未变**

Run: `uv run pytest tests/test_gui.py -q`
Expected: 通过，说明只是视觉和排版变化，没有破坏页面逻辑。

---

## Task 3: 重点美化结果页，让它更像正式报表

**Files:**
- Modify: `src/commission/gui/steps/step_result.py`
- Modify: `tests/test_gui.py`

- [ ] **Step 1: 写结果页文本和按钮布局测试**

确认结果页仍然保留结果区、复制按钮和写入飞书按钮。

```python
from commission.gui.steps.step_result import StepResult


def test_result_page_keeps_action_buttons(qapp):
    step = StepResult()
    assert step.btn_copy.text() == "复制结果"
    assert step.btn_feishu.text() == "写入飞书"
```

- [ ] **Step 2: 运行测试确认当前结果页样式还未达到目标**

Run: `uv run pytest tests/test_gui.py -q`
Expected: 在修改结果页布局前，先确保测试覆盖了按钮与结果区。

- [ ] **Step 3: 给结果页加“摘要 + 明细”两层结构**

把 `QTextEdit` 外层包成内容卡片，并在上方增加一个摘要区，突出：
- 房源类型
- 视角
- 总金额
- 进店实收
- 应发佣金

摘要区用更大字号、更少颜色、更明确的分层。

- [ ] **Step 4: 让业务员拆分区块更清晰**

当前格式化文本保持不变，但结果页外围改成更像报表的展示：
- 主结果摘要
- Step 1~6 分段
- 业务员拆分单独成块
- 复制 / 写入飞书按钮固定在底部

- [ ] **Step 5: 统一结果页操作按钮风格**

- 将“写入飞书”设为主按钮
- 将“复制结果”设为次按钮
- 调整按钮宽度和间距，避免视觉上过于拥挤

- [ ] **Step 6: 跑 GUI 回归测试和 offscreen 启动验证**

Run:
- `uv run pytest tests/test_gui.py -q`
- `QT_QPA_PLATFORM=offscreen uv run python -c "from PySide6.QtWidgets import QApplication; from commission.gui.wizard import CommissionWizard; app = QApplication([]); window = CommissionWizard(); print(type(window).__name__)"`

Expected:
- `tests/test_gui.py` 通过
- 控制台输出 `CommissionWizard`

---

## Task 4: 做一次可视验收和文档收口

**Files:**
- Modify: `README.md`
- Modify: `handoff.md`
- Modify: `docs/architecture-notes.md`
- Modify: `tests/test_gui.py`

- [ ] **Step 1: 补一条 GUI 美化后的说明**

在 README 或 handoff 中补一句：GUI 已做统一视觉优化，保留原有流程和功能。

- [ ] **Step 2: 把架构备注里的 GUI 职责说明更新为当前状态**

`docs/architecture-notes.md` 中补充：GUI 除了负责交互，也已经统一接入视觉样式层，但不承载业务规则。

- [ ] **Step 3: 做一次全量回归**

Run:
- `uv run pytest -q`
- `QT_QPA_PLATFORM=offscreen uv run python -c "from PySide6.QtWidgets import QApplication; from commission.gui.wizard import CommissionWizard; app = QApplication([]); window = CommissionWizard(); print(type(window).__name__)"`

Expected:
- 所有测试通过
- GUI 能在无显示器环境下正常启动

- [ ] **Step 4: 小提交**

建议把 GUI 美化作为单独提交，不和逻辑改动混在一起。

```bash
git add src/commission/gui/styles.py src/commission/gui/*.py tests/test_gui.py README.md handoff.md docs/architecture-notes.md
git commit -m "feat: polish gui visuals"
```

---

## Not touching yet

以下内容在本阶段先不动：

- 不重写 GUI 流程。
- 不替换 PySide6。
- 不引入主题切换系统。
- 不做深色模式。
- 不加动画或复杂动效。
- 不改变计算和写入逻辑。
- 不扩展业务功能。

原因：GUI 美化的目标是提升“看起来像正式工具”的感觉，而不是把项目重做成另一套产品。当前最重要的是统一视觉语言、控制风险、保持行为稳定。

---

## Minimum safe execution order

1. 先抽统一样式入口 `styles.py`
2. 再统一主窗口和步骤页的视觉层次
3. 再重点重做结果页
4. 最后跑回归、做文档收口和提交

每一步都要在对应测试通过后再进入下一步，避免视觉调整影响现有流程。

---

## Verification checklist

- `uv run pytest -q`
- `uv run pytest tests/test_gui.py -q`
- `QT_QPA_PLATFORM=offscreen uv run python -c "from PySide6.QtWidgets import QApplication; from commission.gui.wizard import CommissionWizard; app = QApplication([]); window = CommissionWizard(); print(type(window).__name__)"`
- 人工检查：
  - 主窗口步骤条是否更清晰
  - 输入区是否更整洁
  - 结果页是否更像报表
  - 按钮层级是否明显

---

## Scope gaps to watch

如果后续出现以下需求，应该先单独开新计划，而不是塞进本次美化：

- 主题系统 / 深色模式
- 动画与过渡效果
- 图表化结果展示
- 移动端或 Web 端重做
- 交互流程大改
