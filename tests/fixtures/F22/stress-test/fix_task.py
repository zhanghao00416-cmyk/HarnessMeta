"""修复：用 80 REQ + 50 CON 重新生成 task-stress.md"""
import random
import re
from pathlib import Path

BASE = Path(__file__).parent
random.seed(42)

# 读取 spec 和 arch 获取所有 ID
with open(BASE / "spec-stress.yaml", encoding="utf-8") as f:
    content = f.read()

all_req_ids = re.findall(r"REQ-ORD-\d{3}", content)
all_ac_ids = [f"AC-ORD-{i+1:03d}" for i in range(300)]

with open(BASE / "architecture-stress.yaml", encoding="utf-8") as f:
    arch_content = f.read()
all_con_ids = re.findall(r"CON-ORD-\d{3}", arch_content)

task_req_refs = random.sample(all_req_ids, min(80, len(all_req_ids)))
task_con_refs = random.sample(all_con_ids, min(50, len(all_con_ids)))
task_ac_ids = random.sample(all_ac_ids, 40)

task_md = """---
artifact:
  id: ORD-order-001
  type: task
  title: 订单核心服务实现（大规模版）
  domain: order
  status: active
  version: "1.0.0"
  dependencies:
    - ORD-specs
    - order-architecture
---

# 工单 ORD-order-001：订单核心服务实现

## 需求映射

| 需求 ID | 覆盖程度 |
|---------|---------|
"""
for rid in task_req_refs:
    task_md += f"| {rid} | full |\n"

task_md += """
## 目标

实现订单核心服务，支持订单创建、支付、状态管理。

## 验证步骤

"""
for i, ac_id in enumerate(task_ac_ids):
    task_md += f"""### VAL-ORD-001-{i+1:03d}：验证 {ac_id}

**类型**：automated_test
**命令**：`pytest tests/test_order.py -k test_{i+1} -v`
**预期结果**：测试通过
**验收标准**：{ac_id}

"""

task_md += """
## 约束

### 约束引用

"""
for cid in task_con_refs:
    task_md += f"- {cid}\n"

task_md += """
## 完成定义

- [ ] 所有实现步骤已完成
- [ ] 所有验证步骤已通过
"""

with open(BASE / "task-stress.md", "w", encoding="utf-8") as f:
    f.write(task_md)

print(f"Generated task with {len(task_req_refs)} REQ + {len(task_ac_ids)} AC + {len(task_con_refs)} CON")
print(f"Total references: {len(task_req_refs) + len(task_ac_ids) + len(task_con_refs)}")
