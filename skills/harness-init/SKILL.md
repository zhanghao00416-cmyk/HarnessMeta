---
name: harness-init
description: 初始化项目骨架。读取 project.yaml，生成项目目录结构、meta 模板文件和功能状态清单。
---

# harness-init：项目骨架初始化

## 触发条件

用户提供 `project.yaml` 并要求初始化项目时执行。

## 输入

- `project.yaml`（必须存在）

## 步骤

### 1. 检查 project.yaml 是否存在

**如果不存在**：进入交互式创建模式（步骤 2）。

**如果已存在**：读取并验证必填字段，跳到步骤 3。

### 2. 交互式创建 project.yaml

采用**两轮对话**模式：

**第 1 轮：收集自然语言描述**

向用户提问：

> 描述一下你想做的项目。包括：做什么、用什么技术、有哪些核心功能。随便说，我来帮你整理。

等待用户回答。

**第 2 轮：拆解 + 建议 + 确认**

从用户描述中提取以下信息：

1. **项目名称**：从描述中推断
2. **项目描述**：一句话概括
3. **功能拆解**：将描述拆为功能列表（编号 + 标题 + 依赖）
4. **架构原则**：从技术描述中提取通用原则
5. **部署配置**：从技术栈推断服务组件，默认生成 Docker Compose 部署段
6. **验证命令**：根据技术栈推荐

然后**参考 `templates/reference/feature-catalog.md`**，检查用户可能遗漏的功能，以建议形式展示：

```
AI: 根据你的描述，我整理出以下功能和架构原则：

    功能清单：
    F01 项目骨架
    F02 数据库模型（依赖 F01）
    F03 LLM 网关（依赖 F01）
    F04 对话功能（依赖 F02, F03）

    架构原则：
    1. 分层架构：api → domain → services → infra
    2. LLM 调用通过 Provider 抽象

    验证命令：python -m pytest -x

    🟢 部署架构已默认包含（Docker Compose），将在 harness-specify-arch 阶段生成 DEPLOYMENT.md。

    🟡 根据你的项目类型，你可能还需要：
    - 错误中间件（全局异常拦截）
    - SSE 流式输出（实时返回 LLM 生成内容）
    - 上下文管理（多轮对话历史）
    - 认证与限流（JWT/API Key + 按用户限流）

    需要加入这些吗？或者有其他调整？确认后我就开始生成。
```

用户确认后，生成 project.yaml 并写入项目根目录。

### 3. 验证 project.yaml

读取项目根目录下的 `project.yaml`。检查以下必填字段：

- `project.name`
- `project.description`
- `constitution.principles`（至少 1 条）
- `features`（至少 1 个）
- `deployment.type`（默认为 docker-compose）

缺少必填字段时，报告缺失项并停止。

### 4. 创建目录结构

在项目根目录下创建以下目录：

```
docs/
docs/specs/
docs/specs/_architecture/
docs/meta/
orders/
changes/
changes/_explorations/
changes/archive/
```

### 5. 生成核心 meta 文件（第 1 批：6 个）

从 `templates/meta/` 模板生成以下文件：

| 模板 | 输出路径 | 填充规则 |
|------|---------|--------|
| `AGENTS.md` | `AGENTS.md` | 填入 `verify_commands` 段的健康检查命令 |
| `ARCHITECTURE.md` | `ARCHITECTURE.md` | 填入 `constitution` 段的原则和规则 |
| `QUICK_REFERENCE.md` | `QUICK_REFERENCE.md` | 填入命令和核心规则前 5 条 |
| `progress.md` | `progress.md` | 填入项目名称和创建时间，所有功能标记为 not_started |
| `session-handoff.md` | `session-handoff.md` | 初始化为空状态 |
| `evaluator-rubric.md` | `evaluator-rubric.md` | 直接复制模板 |

### 6. 生成功能状态清单

创建 `feature_list.json`：

```json
{
  "features": [
    {
      "id": "F01",
      "title": "项目骨架",
      "status": "not_started",
      "dependencies": []
    }
  ]
}
```

从 `project.yaml` 的 `features` 段提取所有功能。

### 7. 输出初始化报告

```
## harness-init 完成

项目：{{project_name}}
目录结构：✓
核心 meta 文件：6 个已生成
功能清单：{{feature_count}} 个功能已录入

下一步：执行 /harness-init-docs 生成剩余 5 个工作流文件
（建议在新会话中执行，避免上下文累积影响质量）
```

## 约束

- 不生成工单文件（工单由 harness-order 生成）
- 不填写规格内容（规格由 harness-specify 填写）
- 所有 `{{variable}}` 占位符从 project.yaml 取值
