# 速查卡

> AI 会话快速参考。每次启动会话时首先阅读此文件。

## 关键命令

| 命令 | 用途 |
|------|------|
| `{{health_check_command}}` | 项目健康检查 |
| `{{architecture_check_command}}` | 架构约束检查 |
| `docker compose build` | 构建服务镜像 |
| `docker compose up -d` | 后台启动所有服务 |
| `docker compose down` | 停止并移除所有服务 |

## 关键文件

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | AI 会话协议（必须遵守） |
| `ARCHITECTURE.md` | 架构宪法（不可违反） |
| `docs/specs/_architecture/DEPLOYMENT.md` | 部署架构（服务编排/环境/健康检查） |
| `progress.md` | 当前进度日志 |
| `session-handoff.md` | 会话交接清单 |
| `feature_list.json` | 功能完成状态追踪 |

## 当前状态

- **活跃工单**：{{active_orders}}
- **下一步**：{{next_step}}
- **暂停点**：{{pause_point}}

## 架构速记

```
{{architecture_brief}}
```

## 核心规则（前 5 条）

<!-- 从 constitution.rules 提取前 5 条，编号填入 -->
1. {{rule_1}}
2. {{rule_2}}
3. {{rule_3}}
4. {{rule_4}}
5. {{rule_5}}

---

> 此文件由 `harness-init` 生成，每次工单完成后由 AI 更新"当前状态"段。
