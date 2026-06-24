# 接口/API 变更检查清单

> 仅当变更涉及对外契约（API 路径、请求/响应字段、错误码、SSE 事件）时使用。
> `/harness-apply` 前必须逐项确认；`/harness-verify` 时输出勾选结果。

---

## A. 文档（代码之前）

- [ ] 已明确变更的 **请求方法 + 路径**（或事件类型）
- [ ] 已更新 `docs/specs/{{domain}}/spec.md` 对应章节
- [ ] 若新增/修改错误码：已更新 `ARCHITECTURE.md` 错误码章节
- [ ] 若涉及枚举/默认值：已更新 `docs/meta/FACT_REGISTRY.md`
- [ ] docs 之间 **无字段名冲突**（以 spec.md 为准）

## B. 代码（按分层）

- [ ] 请求/响应模型已对齐规格
- [ ] API 路由层已更新（无业务逻辑渗入）
- [ ] Domain 层编排逻辑已更新
- [ ] Service/Infra 层已更新
- [ ] 未硬编码配置值；未破坏依赖方向

## C. 测试与验证

- [ ] 已添加或更新单测/集成测
- [ ] 验证命令通过（`verify_commands.health_check`）
- [ ] 无 Breaking Change 或已在 proposal 中标注

## D. 交接

- [ ] `feature_list.json` 状态已更新
- [ ] `progress.md` 已恢复主线或指向下一变更
- [ ] `session-handoff.md` 含下一会话开场白
- [ ] 若 Breaking Change：已在 proposal.md 标注需同步项

## 结论

- [ ] **Ready** — 可归档，恢复主线
- [ ] **Not Ready** — 列出阻塞项，保持 `in_progress`
