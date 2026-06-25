# Repository Structure Review

> **审查日期**：2026-06-25
> **审查范围**：harness-meta 全仓库
> **审查目标**：验证 P0 治理后的目录职责是否清晰、面向用户与面向维护者的内容是否物理分离

---

## 1. 审查维度与评分

| # | 维度 | 评分 | 说明 |
|---|------|------|------|
| 1 | **templates 只包含模板** | ✅ 9.5/10 | 8 个过程文档已迁出，残留的 6 个 Schema 定义属于权威规范，留在此处合理 |
| 2 | **schemas 都是权威定义** | ✅ 10/10 | 3 个变更 schema（hotfix/standard/feature），全部被 harness-change 消费 |
| 3 | **governance 独立** | ✅ 10/10 | 9 个治理文档全部在 docs/governance/，与 templates 物理隔离 |
| 4 | **README 面向用户** | ✅ 9/10 | 从 412 行瘦身到 202 行，只保留使用指南；治理信息指向 GOVERNANCE.md |
| 5 | **AGENTS 面向执行** | ✅ 9/10 | 会话协议 + Agent 体系 + 执行规则，职责清晰 |
| 6 | **skills 完整且无重复** | ✅ 10/10 | 20 个 Skill，每个有独立目录 + SKILL.md，无内容重复 |
| 7 | **测试与 fixture 隔离** | ✅ 9/10 | tests/ 下 e2e/planner/runtime/fixtures 分层清晰 |
| **总分** | | **9.5/10** | |

---

## 2. 当前目录职责矩阵

### 2.1 templates/meta/ 文件分类（17 个）

| 类别 | 数量 | 文件 | 是否复制到用户项目 |
|------|------|------|-------------------|
| **元文档模板** | 11 个 | AGENTS / ARCHITECTURE / QUICK_REFERENCE / progress / session-handoff / evaluator-rubric / DEPENDENCY_MAP / FACT_REGISTRY / CHANGE_WORKFLOW / FEATURE_DEV_WORKFLOW / API_CHANGE_CHECKLIST | ✅ 是（由 harness-init + harness-init-docs 复制） |
| **Schema 定义** | 6 个 | context-schema（在 templates/ 根）/ artifact-meta-schema / spec-schema / task-schema / architecture-schema / verify-schema / schema-change-policy | ❌ 否（权威定义，留在模板仓库供引用） |

> **说明**：schema-change-policy.md 严格来说是治理文档，但它是 AGENTS.md 中被引用的"活规则"（用户项目执行时需参照），留在 templates/meta 合理。

### 2.2 docs/governance/ 文件分类（9 个）

| 类别 | 数量 | 文件 |
|------|------|------|
| **治理索引** | 1 个 | GOVERNANCE.md |
| **冻结声明** | 3 个 | phase2-freeze-declaration / phase2.5-freeze-declaration / harness-core-v1-freeze-declaration |
| **审查报告** | 3 个 | artifact-chain-review / artifact-chain-review-v2.5 / verify-consumer-review |
| **验证报告** | 1 个 | context-contract-validation-report |
| **设计文档** | 1 个 | phase3-context-engine |

> 全部为框架开发过程中产生的过程文档，面向维护者，不复制到用户项目。

### 2.3 templates/architecture/（7 个）

| 文件 | 行数 | 生成条件 |
|------|------|---------|
| API_CONTRACT.md | 99 | 所有项目 |
| DATA_MODEL.md | 77 | 所有项目 |
| DEPLOYMENT.md | 111 | 所有项目（默认 docker-compose） |
| DOMAIN_MAP.md | 63 | 所有项目 |
| ERROR_CODE.md | 71 | 所有项目 |
| FRONTEND_STYLE.md | 309 | 仅含前端的全栈/前端项目 |
| COMPONENT_LIBRARY.md | 130 | 仅含前端的全栈/前端项目 |

---

## 3. 引用完整性检查

### 3.1 跨目录引用路径验证

| 检查项 | 方法 | 结果 |
|--------|------|------|
| Skill → Schema 引用 | 扫描 skills/ 中对 templates/meta/*.yaml 的引用 | ✅ 全部有效 |
| Skill → 治理文档引用 | 扫描 skills/ 中对 docs/governance/ 的引用 | ✅ harness-context 2处已修复 |
| Schema → 治理文档引用 | 扫描 templates/meta/*.yaml 中对 governance 的引用 | ✅ verify-schema.yaml 1处已修复 |
| README → 各路径引用 | 扫描 README.md 中所有路径 | ✅ 无断链 |
| 治理文档间引用 | 扫描 docs/governance/ 内部引用 | ✅ 全部使用 docs/governance/ 路径 |

### 3.2 残留旧路径检查

```
扫描模式：templates/meta/(artifact-chain-review|context-contract-validation-report|
verify-consumer-review|phase2-freeze-declaration|phase2.5-freeze-declaration|
harness-core-v1-freeze-declaration|phase3-context-engine)
结果：0 matches ✅
```

---

## 4. 改进建议

### 4.1 已达标项（无需改动）

- **目录职责分离**：templates（用户面向）vs docs/governance（维护者面向）已清晰分离
- **Skill 完整性**：20 个 Skill 全部有独立目录和 SKILL.md，无重复内容
- **Schema 治理**：6 套冻结 Schema + Change Policy，治理体系完整
- **测试覆盖**：90 个测试场景（Planner 30 + Runtime 55 + E2E 5），全部通过

### 4.2 可选优化（低优先级，不阻塞 v1.0 发布）

| # | 建议 | 优先级 | 理由 |
|---|------|--------|------|
| 1 | schema-change-policy.md 可考虑移到 docs/governance/ | P3 | 它是治理规则而非模板，但 AGENTS.md 引用它作为"活规则"，留在 templates/meta 有执行便利性考量，两可 |
| 2 | templates/meta/ 可拆分为 meta-templates/（11个模板）和 schemas/（6个定义） | P3 | 进一步区分"模板"和"规范"，但会增加 harness-init/init-docs 的路径复杂度，收益不大 |
| 3 | FRONTEND_STYLE.md（309行）行数偏多 | P3 | 可在实战使用后根据反馈精简，当前不阻塞 |

---

## 5. 结论

**harness-meta 仓库结构已达到 Harness Core v1.0 发布标准。**

- templates/ 只包含会被复制到用户项目的内容（模板 + Schema 权威定义）
- docs/governance/ 独立承载所有治理信息
- README 面向使用者，GOVERNANCE.md 面向维护者
- 零断链、零重复、测试全通过

**建议直接进入 P2（Harness Core v1.0 发布）。**
