---
name: harness-adopt-scan
description: 已有代码接入（阶段 1）。扫描已有代码库，反推项目结构、功能清单、架构原则，生成 project.yaml + 目录结构 + 全部 meta 文件。所有功能标记为 passing。
---

# harness-adopt-scan：已有代码接入（扫描与骨架生成）

## 触发条件

用户已有代码库，希望将其纳入 harness 管理体系时执行。

## 输入

- 已有代码库（项目根目录）
- `harness-meta/` 模板文件

## 前置检查

读取项目根目录，确认以下条件：

- 项目根目录存在源代码文件（src/、app/、lib/ 或类似目录）
- `project.yaml` 不存在（若已存在，提示"已接入 harness，请使用 Flow B 变更流程"）
- `AGENTS.md` 不存在（若已存在，同上）

如果已接入，终止并提示用户使用 Flow B。

## 步骤

### 0. 扫描代码库（只读分析）

进入**纯只读模式**，扫描项目根目录：

**必须分析的内容**：

| 分析项 | 方法 | 产出 |
|--------|------|------|
| 技术栈 | 读 package.json / pyproject.toml / go.mod / Cargo.toml 等 | 语言、框架、依赖 |
| 目录结构 | 扫描顶层和二级目录 | 模块划分、分层模式 |
| 入口文件 | 读 main/app/index 等入口 | 应用类型、启动方式 |
| 配置文件 | 读 .env / config / settings | 配置管理方式 |
| 测试文件 | 扫描 test/ / tests/ / *_test.* | 测试框架、验证命令 |
| 构建脚本 | 读 Makefile / Dockerfile / package.json scripts | 构建和部署命令 |

**深度分析（按需）**：

- 读路由定义文件 → 提取 API 端点
- 读数据模型文件 → 提取表结构和关系
- 读中间件/拦截器 → 提取错误处理模式
- 读领域逻辑文件 → 提取业务域划分

### 1. 反推功能清单

从代码分析中拆解功能列表：

**拆解规则**：

- 按业务域分组（auth、payment、chat 等）
- 每个独立模块/功能对应一个 feature
- 基础设施（骨架、配置、错误处理）单独列出
- 推断功能间的依赖关系

```
示例输出：
F01 项目骨架（无依赖）
F02 数据库模型（依赖 F01）
F03 错误中间件（依赖 F01）
F04 用户认证（依赖 F02, F03）
F05 对话功能（依赖 F02, F04）
```

### 2. 反推架构原则

从代码模式中归纳架构原则：

- 分层依赖方向（从目录结构和 import 关系推断）
- 外部服务抽象方式（是否有 Provider/Adapter 模式）
- 配置管理方式（环境变量 / 配置文件 / 硬编码）
- 错误处理边界（全局异常处理 / 局部 try-catch）
- 接口契约模式（RESTful / GraphQL / RPC）

### 3. 交互确认

向用户展示分析结果，请求确认：

```
## 代码库分析结果

技术栈：{{language}} {{framework}} {{version}}
模块数：{{module_count}} 个
入口文件：{{entry_files}}

### 功能清单（{{feature_count}} 个）
{{feature_list}}

### 架构原则（从代码推断）
{{principles}}

### 验证命令（从构建脚本推断）
{{verify_commands}}

以上是否准确？有需要调整的吗？
确认后我将生成 project.yaml 和项目骨架文件。
```

用户确认后，进入生成阶段。

### 4. 生成 project.yaml

使用交互确认后的数据，生成 `project.yaml`：

- `project.name`：从项目配置文件或目录名推断
- `project.description`：从 README 或代码注释推断，无则让用户提供
- `constitution.principles`：步骤 2 推断的架构原则
- `constitution.rules`：从代码规范推断
- `features`：步骤 1 的功能清单
- `change_management`：使用默认配置
- `verify_commands`：从构建脚本推断
- `context`：技术栈摘要

### 5. 创建目录结构

在项目根目录下创建 harness 所需目录（如不存在）：

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

### 6. 生成核心 meta 文件（第 1 批：6 个）

从 `templates/meta/` 模板生成以下文件：

| 模板 | 输出路径 | 填充规则 |
|------|---------|--------|
| `AGENTS.md` | `AGENTS.md` | 填入从代码推断的验证命令 |
| `ARCHITECTURE.md` | `ARCHITECTURE.md` | 填入反推的架构原则和规则 |
| `QUICK_REFERENCE.md` | `QUICK_REFERENCE.md` | 填入命令和核心规则前 5 条 |
| `progress.md` | `progress.md` | 填入项目名称和时间，所有功能标记为 passing |
| `session-handoff.md` | `session-handoff.md` | 初始化为"代码接入完成"状态 |
| `evaluator-rubric.md` | `evaluator-rubric.md` | 直接复制模板 |

### 7. 生成功能状态清单

创建 `feature_list.json`，所有功能标记为 `passing`：

```json
{
  "features": [
    {
      "id": "F01",
      "title": "项目骨架",
      "status": "passing",
      "dependencies": [],
      "evidence": "src/ 目录结构已存在"
    }
  ]
}
```

### 8. 输出完成报告

```
## harness-adopt-scan 完成

项目：{{project_name}}
技术栈：{{tech_stack}}
功能清单：{{feature_count}} 个（全部 passing）
核心 meta 文件：6 个已生成

下一步：执行 /harness-adopt-spec 生成规格文档（建议新会话）
```

## 约束

- 阶段 0 严格只读，不修改任何已有代码文件
- 不生成规格文档（由 harness-adopt-spec 生成）
- 不生成工单文件（代码已实现，无需工单）
- 所有功能状态标记为 `passing`（代码已实现并运行）
- 功能清单和架构原则必须经用户确认后才生成文件
- 所有 `{{variable}}` 占位符从代码分析结果取值
