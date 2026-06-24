---
name: harness-analyze
description: 跨文档一致性审计。在工单生成后、执行前，扫描规格→工单之间的覆盖缺口、术语漂移、路径不一致。只读不改文件。
---

# harness-analyze：跨文档一致性审计

## 触发条件

harness-order 完成后，harness-execute 之前执行。用户要求审计一致性时触发。

## 输入

- `project.yaml`（features 段完整）
- `docs/specs/`（域规格 + 架构规格）
- `orders/`（已生成的工单文件）
- `docs/meta/DEPENDENCY_MAP.md`

## 约束

- **严格只读**：不修改任何文件，只输出审计报告
- **ARCHITECTURE.md 是最高权威**：架构约束冲突自动标记为 CRITICAL
- **发现上限 50 条**：超出部分汇总在溢出摘要中

## 步骤

### 0. 前置检查

确认所有工单已生成（扫描 `orders/` 目录）。若有缺失，报告"工单不完整，请先运行 /harness-order 补齐"，终止审计。

### 1. 加载文档（渐进式，按需读取）

**必读**：
- `project.yaml` → features 列表、constitution
- `ARCHITECTURE.md` → 分层规则、禁止清单
- `docs/meta/DEPENDENCY_MAP.md` → 依赖关系表

**按需读取**（检测路径存在才读）：
- `docs/specs/` → 域规格（行为定义）
- `docs/specs/_architecture/` → 架构规格（API_CONTRACT / DATA_MODEL / DOMAIN_MAP / ERROR_CODE）
- `orders/*.md` → 逐个读取，提取元数据 + 功能三元组 + 实现清单

### 2. 构建语义模型

从加载的文档中提取结构化数据（内部使用，不输出）：

| 模型 | 来源 | 用途 |
|------|------|------|
| 需求清单 | features + 域规格 | 逐项检查是否被工单覆盖 |
| 工单清单 | orders/*.md | 逐项检查是否对应某个需求 |
| 术语表 | ARCHITECTURE + DOMAIN_MAP | 检查跨文档命名一致性 |
| 路径清单 | 工单实现清单 + DATA_MODEL | 检查文件路径是否冲突 |

### 3. 检测扫描（6 个维度）

#### A. 覆盖缺口

- 需求无对应工单（CRITICAL）
- 工单无对应需求（HIGH）
- 架构规格中定义的端点/表未被任何工单实现（MEDIUM）

#### B. 术语漂移

- 同一概念在不同文档中命名不同（如 "用户会话" vs "对话" vs "session"）（MEDIUM）
- 工单标题与 feature title 不一致（LOW）

#### C. 路径冲突

- 两个工单修改同一文件但未声明依赖（HIGH）
- 工单实现清单引用不存在的目录结构（MEDIUM）

#### D. 架构合规

- 工单实现计划违反 ARCHITECTURE.md 分层规则（CRITICAL）
- 工单引用了禁止清单中的模式（CRITICAL）

#### E. 错误码一致性

- 工单中的错误码不在 ERROR_CODE.md 分配的域范围内（HIGH）
- 多个工单分配相同错误码（HIGH）

#### F. 依赖完整性

- 工单声明的依赖工单不存在（CRITICAL）
- 工单依赖顺序与 DEPENDENCY_MAP 不一致（HIGH）

### 4. 严重度分级

| 级别 | 含义 | 处理建议 |
|------|------|---------|
| **CRITICAL** | 阻塞执行，必须先修 | 修改工单或规格后再执行 |
| **HIGH** | 高风险，执行中大概率出问题 | 强烈建议先修 |
| **MEDIUM** | 中风险，执行中需要人工判断 | 执行时注意 |
| **LOW** | 风格/措辞改进 | 可忽略 |

> **与 harness-verify 严重度差异说明**：analyze 是规格层审计（工单生成前，用 4 级 CRITICAL/HIGH/MEDIUM/LOW），verify 是实现层验证（代码完成后，用 3 级 CRITICAL/WARNING/SUGGESTION）。两者作用阶段不同，故严重度词汇表不同。

### 5. 输出审计报告

```markdown
## 一致性审计报告

审计时间：{{timestamp}}
工单数：{{order_count}} | 需求数：{{feature_count}}

### 发现汇总

| 级别 | 数量 |
|------|------|
| CRITICAL | {{critical_count}} |
| HIGH | {{high_count}} |
| MEDIUM | {{medium_count}} |
| LOW | {{low_count}} |

### 详细发现

| ID | 维度 | 级别 | 位置 | 描述 | 建议 |
|----|------|------|------|------|------|
| A1 | 覆盖缺口 | CRITICAL | F05 规格 | 知识库分块上传需求无对应工单 | 补充工单 F15a |
| C1 | 路径冲突 | HIGH | F02/F09 | 两工单均修改 app/core/config.py 但未声明依赖 | F09 添加 F02 依赖 |

### 覆盖率

| 指标 | 值 |
|------|-----|
| 需求覆盖率 | {{coverage_pct}}%（{{covered}}/{{total}}） |
| 工单对应率 | {{order_match_pct}}% |
| 术语一致性 | {{term_consistency}} |

### 下一步

<!-- 根据 critical_count 实际值选择输出一段 -->
若存在 CRITICAL 问题：
⚠️ 存在 {{critical_count}} 个 CRITICAL 问题，建议修复后再执行工单。

若无 CRITICAL 问题：
✅ 无 CRITICAL 问题，可以开始执行工单。

建议执行顺序：
1. 修复 CRITICAL（{{critical_count}} 个）
2. 修复 HIGH（{{high_count}} 个）
3. 开始执行：/harness-execute {{first_order_id}}
```

### CRITICAL 问题回退路径

当审计报告存在 CRITICAL 问题时，按以下规则回退到对应 Skill 修复：

| CRITICAL 类型 | 回退目标 | 操作 |
|-------------|----------|------|
| 覆盖缺口（需求无工单） | harness-order | 补生成缺失工单，更新 DEPENDENCY_MAP |
| 覆盖缺口（工单无需求） | harness-clarify + harness-specify | 补澄清需求，更新域规格 |
| 依赖完整性 | harness-order | 修正 DEPENDENCY_MAP 表 1/表 2 |
| 架构合规 | harness-specify-arch | 修正架构规格约束 |

> analyze 本身不修改任何文件，只输出报告。回退操作需要用户手动执行对应 Skill。

## 完成条件

- [ ] 所有已生成工单已扫描
- [ ] 6 个维度检测完成
- [ ] 审计报告已输出
- [ ] 下一步建议已给出
