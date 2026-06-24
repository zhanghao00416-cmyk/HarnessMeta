---
name: harness-specify-arch
description: 架构规格生成。根据 project.yaml 和已生成的域规格，生成 5 个全局架构规格文件并更新事实注册表。建议在 harness-specify 完成后，在新会话中执行。
---

# harness-specify-arch：架构规格生成

## 触发条件

harness-specify 完成后执行。建议在新会话中执行，以获得最佳生成质量。

## 输入

- `project.yaml`（features 段和 constitution 段完整）
- `docs/specs/{{domain}}/spec.md`（域规格已由 harness-specify 生成）
- `templates/architecture/`（架构规格模板）

## 前置检查

读取项目根目录，确认以下条件：

- `project.yaml` 存在
- `docs/specs/` 下至少有一个域规格文件（harness-specify 已执行）

如果缺失，提示用户先执行 `/harness-specify`。

## 步骤

### 1. 读取上下文

从以下来源收集信息：

- `project.yaml`：features 段（功能清单）+ constitution 段（架构原则和规则）+ deployment 段（部署配置）
- `docs/specs/*/spec.md`：已生成的域规格（提取需求名称、场景、接口定义）

### 2. 生成架构规格文件

在 `docs/specs/_architecture/` 下生成 5 个文件，使用 `templates/architecture/` 模板：

| 模板 | 输出路径 | 填充规则 |
|------|---------|--------|
| `API_CONTRACT.md` | `docs/specs/_architecture/API_CONTRACT.md` | 根据 features 提取端点、请求/响应格式、SSE 事件 |
| `DATA_MODEL.md` | `docs/specs/_architecture/DATA_MODEL.md` | 根据 features 提取表结构、缓存 key、向量集合 |
| `DEPLOYMENT.md` | `docs/specs/_architecture/DEPLOYMENT.md` | 根据 `deployment` 段提取服务编排、Dockerfile 规范、环境变量映射、健康检查 |
| `DOMAIN_MAP.md` | `docs/specs/_architecture/DOMAIN_MAP.md` | 根据 features 和 constitution 提取域职责、分层规则、禁止清单 |
| `ERROR_CODE.md` | `docs/specs/_architecture/ERROR_CODE.md` | 根据 features 分配域编码范围、注册错误码 |

这些文档是**全局级**规格，不属於某个业务域，但所有域规格都引用它们。

**生成规则**：

- 读取每个域规格中的需求和场景，提取架构相关信息
- 确保架构规格与域规格的术语一致（接口名、域名、错误码等）
- 使用 `[TBD: filled by Fxx]` 标记需要工单实现时填充的内容

### 3. 更新事实注册表

读取已生成的全部规格文档（域规格 + 架构规格），更新 `docs/meta/FACT_REGISTRY.md`：

- 将每个规格文件对应的权威事实类别填入「源文件索引」表
- 更新「高频易错事实」中的项目特定条目

### 4. 输出完成报告

```
## 架构规格生成完成

已生成：5 个架构规格文件
- API_CONTRACT.md（{{endpoint_count}} 个端点）
- DATA_MODEL.md（{{table_count}} 张表）
- DEPLOYMENT.md（{{service_count}} 个服务）
- DOMAIN_MAP.md（{{domain_count}} 个域）
- ERROR_CODE.md（{{error_count}} 个错误码）

已更新：FACT_REGISTRY.md 源文件索引

全部规格文档就绪。

下一步：执行 /harness-order 生成工单
```

## 约束

- 不修改 project.yaml
- 不修改已有的域规格文件（由 harness-specify 生成）
- 不生成工单文件
- 不写代码
- 架构规格与域规格的术语必须一致
