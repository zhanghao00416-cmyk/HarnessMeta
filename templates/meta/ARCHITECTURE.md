# 架构宪法

> 此文件定义项目的不可协商原则。
> 所有工单实现必须遵守，违反即为缺陷。

---

## 项目概览

- **项目名称**：{{project_name}}
- **项目描述**：{{project_description}}
- **技术栈**：{{tech_stack}}

---

## 核心原则

<!-- 从 project.yaml 的 constitution.principles 逐条填入，编号从 1 开始 -->
1. {{principle_1}}
2. {{principle_2}}
3. {{principle_3}}
...

---

## 分层架构

```
{{architecture_layers}}
```

### 依赖方向

{{dependency_direction}}

### 层级职责

| 层 | 职责 | 允许依赖 |
|----|------|---------|
| {{layer_name}} | {{responsibility}} | {{allowed_deps}} |

---

## 架构规则

<!-- 从 project.yaml 的 constitution.rules 逐条填入，编号从 1 开始 -->
1. **{{rule_name_1}}**：{{rule_description_1}}
2. **{{rule_name_2}}**：{{rule_description_2}}
...

---

## 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| {{naming_type}} | {{convention}} | {{example}} |

---

## 目录结构

```
{{project_structure}}
```

---

## 关键决策

| 决策 | 选择 | 原因 |
|------|------|------|
| {{decision}} | {{choice}} | {{reason}} |

---

> 此文件由 `project.yaml` 的 `constitution` 段生成。
> 如需修改架构原则，修改 `project.yaml` 后重新生成。
