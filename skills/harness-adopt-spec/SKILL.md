---
name: harness-adopt-spec
description: 已有代码接入（阶段 2）。从已有代码反推生成域规格文档和架构规格文档，更新事实注册表。建议在 harness-adopt-scan 完成后，在新会话中执行。
---

# harness-adopt-spec：已有代码接入（规格文档生成）

## 触发条件

harness-adopt-scan 完成后执行。建议在新会话中执行，以获得最佳生成质量。

## 输入

- `project.yaml`（features 段已由 harness-adopt-scan 生成）
- 已有代码库（源代码文件）
- `templates/specs/spec.md`（域规格模板）
- `templates/architecture/`（架构规格模板）

## 前置检查

读取项目根目录，确认以下条件：

- `project.yaml` 存在且 features 段非空
- `ARCHITECTURE.md` 存在（harness-adopt-scan 已执行）
- `feature_list.json` 存在且所有功能状态为 `passing`

如果缺失，提示用户先执行 `/harness-adopt-scan`。

## 步骤

### 1. 读取上下文

从以下来源收集信息：

- `project.yaml`：features 段（功能清单）+ constitution 段（架构原则）
- `ARCHITECTURE.md`：分层规则和约束
- 已有代码文件：按功能分组读取相关源代码

### 2. 按域分组

将功能按业务域分组。域从代码的目录结构推断：

```
src/auth/     → 域 = auth
src/payment/  → 域 = payment
src/chat/     → 域 = chat
```

如果代码不按域分目录，从 import 关系和功能职责推断。

### 3. 生成域规格文档

对每个域，读取对应代码文件，使用 `templates/specs/spec.md` 模板反向生成规格：

**反向生成规则**：

- 从代码中的函数签名、类定义、路由装饰器提取行为描述
- 从代码中的异常处理、条件分支提取边界条件
- 从代码中的注释、docstring 提取意图
- 边界条件转化为场景（前置/当/则格式）
- 每个需求至少一个场景
- 禁止写实现细节（只写行为契约）

**文件路径**：`docs/specs/{{domain}}/spec.md`

### 4. 生成架构规格文件

在 `docs/specs/_architecture/` 下生成 5 个后端 + 2 个前端架构文件（共 7 个），使用 `templates/architecture/` 模板：

| 模板 | 输出路径 | 反向提取规则 |
|------|---------|-------------|
| `API_CONTRACT.md` | `docs/specs/_architecture/API_CONTRACT.md` | 从路由定义、控制器装饰器提取端点、请求/响应格式 |
| `DATA_MODEL.md` | `docs/specs/_architecture/DATA_MODEL.md` | 从 ORM 模型、migration 文件提取表结构和关系 |
| `DEPLOYMENT.md` | `docs/specs/_architecture/DEPLOYMENT.md` | 从 Dockerfile / docker-compose.yml / 环境变量配置提取服务编排和部署架构 |
| `DOMAIN_MAP.md` | `docs/specs/_architecture/DOMAIN_MAP.md` | 从目录结构、import 关系提取域职责和分层规则 |
| `ERROR_CODE.md` | `docs/specs/_architecture/ERROR_CODE.md` | 从异常类定义、错误处理代码提取错误码体系 |
| `FRONTEND_STYLE.md` | `docs/specs/_architecture/FRONTEND_STYLE.md` | 从前端代码提取技术栈、目录结构、命名规范、API 调用层、状态管理、路由、样式、测试规范（仅全栈/前端项目生成） |
| `COMPONENT_LIBRARY.md` | `docs/specs/_architecture/COMPONENT_LIBRARY.md` | 从前端代码提取通用组件、布局组件、业务组件需求，登记组件注册表（仅全栈/前端项目生成） |

**生成规则**：

- 读取代码中的实际实现，提取架构相关信息
- 确保架构规格与代码实现一致（不是理想化设计，而是代码事实）
- 如果代码中某部分架构不规范，在规格中如实记录，用 `[注意: 代码实现与最佳实践不一致]` 标注
- **前端架构规格（FRONTEND_STYLE.md、COMPONENT_LIBRARY.md）仅在项目包含前端代码时生成**：扫描是否存在前端目录（`frontend/`、`src/components/`、`src/pages/`、`src/views/`）或前端配置文件（`package.json` 含 Vue/React 依赖）。如为纯后端项目，跳过这两个文件

### 5. 生成工作流 meta 文件（5 个）

从 `templates/meta/` 模板生成以下文件到 `docs/meta/`：

| 模板 | 输出路径 | 填充规则 |
|------|---------|--------|
| `DEPENDENCY_MAP.md` | `docs/meta/DEPENDENCY_MAP.md` | 根据 features 依赖图 + 代码实际 import 关系填充 |
| `FACT_REGISTRY.md` | `docs/meta/FACT_REGISTRY.md` | 注册所有规格文件为权威事实源 |
| `CHANGE_WORKFLOW.md` | `docs/meta/CHANGE_WORKFLOW.md` | 填入 `change_management` 段配置 |
| `FEATURE_DEV_WORKFLOW.md` | `docs/meta/FEATURE_DEV_WORKFLOW.md` | 填入项目配置 |
| `API_CHANGE_CHECKLIST.md` | `docs/meta/API_CHANGE_CHECKLIST.md` | 直接复制模板 |

### 6. 创建规格目录骨架

根据步骤 2 的域分组，确认 `docs/specs/` 下的域目录已创建。

### 7. 输出完成报告

```
## harness-adopt-spec 完成

项目：{{project_name}}
域规格：{{domain_count}} 个已生成
- auth/spec.md（{{req_count}} 个需求，{{scenario_count}} 个场景）
- chat/spec.md（...）

架构规格：7 个已生成（或 5 个，纯后端项目跳过前端规格）
- API_CONTRACT.md（{{endpoint_count}} 个端点）
- DATA_MODEL.md（{{table_count}} 张表）
- DEPLOYMENT.md（{{service_count}} 个服务）
- DOMAIN_MAP.md（{{domain_count}} 个域）
- ERROR_CODE.md（{{error_count}} 个错误码）
- FRONTEND_STYLE.md（前端规范，如适用）
- COMPONENT_LIBRARY.md（组件注册表，如适用）

工作流 meta 文件：5 个已生成
全部 11 个 meta 文件就绪。

✅ 项目已完整接入 harness 管理体系。
后续改代码请使用 Flow B：/harness-change → /harness-apply → /harness-verify → /harness-archive
```

## 约束

- 不修改已有代码文件
- 不修改 `project.yaml`
- 不修改 harness-adopt-scan 已生成的 meta 文件
- 不生成工单文件
- 规格文档从代码事实反推，不添加代码中不存在的功能
- 架构规格如实记录代码现状，不规范之处用标注标记
- 所有 `{{variable}}` 占位符从代码分析结果取值
