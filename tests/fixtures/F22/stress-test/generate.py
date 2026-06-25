"""Validation-3 压力测试数据生成器 v2 — 大容量版。

目标：生成足够大的 Spec + Architecture，使 Context Bundle 超过 25000 token，
     触发 P2 Budget 裁减机制。

规模：
- 300 个 Requirement（每个含 2 scenario × 2 AC = 4 条 AC 描述，~400 字/条）
- 80 个 Architecture Constraint
- 1 个 Task，引用 80 个 requirement + 40 个 AC + 50 个 constraint
- 15 个 ADR

估算：
- Spec 全部加载: ~300 * 400 字 = 120,000 字 ≈ 240,000 tokens
- 但 Context Builder 只取 Task 引用的 80 个 REQ: ~80 * 400 = 32,000 字 ≈ 64,000 tokens
- 加上 40 AC + 50 CON + ADR + project state ≈ 额外 20,000 字 ≈ 40,000 tokens
- 总计 ~104,000 tokens → 远超 25,000 上限 → 触发 P2 Budget
"""

import random
import yaml
from pathlib import Path

OUT_DIR = Path(__file__).parent
random.seed(42)

DOMAIN = "ORD"

# 长描述模板（~200 中文字）
LONG_DESC = (
    "用户可以通过{渠道}完成{操作}。系统需要在{条件}下保证{质量}。"
    "具体要求包括：1) 接口响应时间不超过{延迟}ms；2) 并发支持{QPS} TPS；"
    "3) 数据一致性通过{一致性}保证；4) 异常情况通过{容错}处理；"
    "5) 所有操作记录审计日志到{日志系统}；6) 敏感数据通过{加密}加密存储。"
    "该需求关联的业务价值：{价值}。"
)

CHANNELS = ["Web 前端", "移动 App", "微信小程序", "OpenAPI", "管理后台"]
OPS = ["创建订单", "支付订单", "取消订单", "查询订单", "退款申请",
       "修改地址", "申请发票", "评价商品", "物流查询", "批量操作"]
CONDS = ["高并发场景", "网络异常场景", "数据库主从切换", "第三方服务超时",
         "消息队列堆积", "缓存穿透", "分布式事务"]
QUALITIES = ["最终一致性", "强一致性", "99.99% 可用性", "P95 < 200ms",
             "零数据丢失", "幂等性", "可回滚"]
CONSISTENCY = ["两阶段提交", "TCC 补偿", "Saga 模式", "本地消息表",
               "可靠事件", "AT 模式"]
FAULTS = ["重试 3 次", "降级为异步", "熔断器", "限流器",
          "兜底缓存", "人工介入"]
LOGS = ["ELK 集群", "阿里云 SLS", "腾讯云 CLS", "自建 Kafka", "Loki"]
ENCRYPTS = ["AES-256-GCM", "国密 SM4", "RSA-2048", "信封加密"]
VALUES = ["提升用户体验", "降低运维成本", "满足合规要求", "支持业务增长",
          "减少客诉", "提高转化率", "降低退款率"]

def make_long_desc(i):
    return LONG_DESC.format(
        渠道=random.choice(CHANNELS),
        操作=random.choice(OPS),
        条件=random.choice(CONDS),
        质量=random.choice(QUALITIES),
        延迟=random.choice([100, 200, 500, 1000]),
        QPS=random.choice([100, 500, 1000, 5000, 10000]),
        一致性=random.choice(CONSISTENCY),
        容错=random.choice(FAULTS),
        日志系统=random.choice(LOGS),
        加密=random.choice(ENCRYPTS),
        价值=random.choice(VALUES),
    )

# ==================== 生成 300 Requirements ====================
def generate_requirements(count=300):
    reqs = []
    for i in range(count):
        title = f"订单功能需求 {i+1}"
        desc = make_long_desc(i)
        reqs.append({
            "id": f"REQ-{DOMAIN}-{i+1:03d}",
            "title": title,
            "description": desc,
            "priority": random.choice(["must", "should", "could"]),
            "category": random.choice(["functional", "non_functional", "performance", "security", "reliability"]),
            "scenarios": [
                {
                    "id": f"SC-REQ-{DOMAIN}-{i+1:03d}-01",
                    "given": f"前置条件：用户已登录，{random.choice(CONDS)}",
                    "when": f"触发动作：用户通过{random.choice(CHANNELS)}{random.choice(OPS)}",
                    "then": f"预期结果：操作成功，{random.choice(QUALITIES)}",
                    "acceptance_criteria": [
                        f"AC-{i+1}-01：接口响应时间 ≤ {random.choice([100,200,500])}ms",
                        f"AC-{i+1}-02：错误率 ≤ 0.1%",
                        f"AC-{i+1}-03：审计日志完整记录",
                    ]
                },
                {
                    "id": f"SC-REQ-{DOMAIN}-{i+1:03d}-02",
                    "given": f"前置条件：{random.choice(CONDS)}",
                    "when": f"触发动作：{random.choice(FAULTS)}",
                    "then": f"预期结果：系统自动恢复，{random.choice(QUALITIES)}",
                    "acceptance_criteria": [
                        f"AC-{i+1}-04：异常恢复时间 ≤ 30s",
                        f"AC-{i+1}-05：数据不丢失",
                    ]
                }
            ]
        })
    return reqs

# ==================== 生成 80 Constraints ====================
CON_TYPES = ["architecture", "security", "data", "reliability", "performance",
             "compliance", "testing", "deployment"]
CON_SEVS = ["block", "warning", "info"]
CON_VERIFS = ["code_review", "static_analysis", "automated_test", "manual_review"]

CON_RULES = [
    "Service 层不得直接访问数据库，必须通过 Repository 接口",
    "所有 API 端点必须通过 JWT Token 认证",
    "订单状态变更必须在数据库事务中完成",
    "支付回调接口必须实现幂等处理",
    "订单查询接口 P95 响应时间 ≤ {t}ms",
    "下单接口支持 ≥ {q} TPS 并发",
    "所有订单操作必须记录审计日志到 {l}",
    "订单数据必须保留 ≥ {y} 年",
    "Service 层单元测试覆盖率 ≥ 80%",
    "用户手机号在日志中必须脱敏显示",
    "外部服务调用超时时间 ≤ {t}ms",
    "热数据必须缓存到 Redis，TTL = {ttl}s",
    "数据库连接池最大连接数 = {n}",
    "消息队列消费必须支持手动 ACK",
    "定时任务必须支持分布式锁，防止重复执行",
    "敏感配置（密钥/密码）不得硬编码，必须走配置中心",
    "API 响应必须统一使用 {{code: 0, data: ..., msg: ...}} 格式",
    "分页查询必须限制最大 page_size ≤ 100",
    "文件上传必须校验类型白名单和大小限制",
    "跨服务调用必须携带 trace_id 实现链路追踪",
]

def make_rule(i):
    tmpl = random.choice(CON_RULES)
    return tmpl.format(
        t=random.choice([100, 200, 500, 1000, 3000, 5000]),
        q=random.choice([100, 500, 1000, 5000]),
        l=random.choice(LOGS),
        y=random.choice([3, 5, 7, 10]),
        ttl=random.choice([60, 300, 600, 3600]),
        n=random.choice([10, 20, 50, 100]),
    )

def generate_constraints(count=80):
    cons = []
    for i in range(count):
        cons.append({
            "id": f"CON-{DOMAIN}-{i+1:03d}",
            "type": random.choice(CON_TYPES),
            "rule": make_rule(i),
            "severity": random.choice(CON_SEVS),
            "verification": random.choice(CON_VERIFS),
        })
    return cons

# ==================== 生成 ====================

requirements = generate_requirements(300)
constraints = generate_constraints(80)

# Task 引用：80 REQ + 40 AC + 50 CON = 170 条引用
all_req_ids = [r["id"] for r in requirements]
all_con_ids = [c["id"] for c in constraints]

task_req_refs = random.sample(all_req_ids, 80)
task_con_refs = random.sample(all_con_ids, 50)
task_ac_ids = [f"AC-ORD-{i:03d}" for i in random.sample(range(1, 301), 40)]

# Spec
spec_ac_list = [
    {"id": f"AC-ORD-{i+1:03d}",
     "description": f"全局验收标准 {i+1}：系统在指定条件下满足功能和性能要求",
     "verification_method": random.choice(["automated_test", "performance_test", "code_review"])}
    for i in range(300)
]

spec = {
    "artifact": {"id": "ORD-specs", "type": "spec", "title": "电商订单系统规格（大规模版）", "domain": "order",
                 "status": "reviewed", "version": "1.0.0"},
    "overview": "超大规模电商订单系统规格，包含 300 个需求。用于 Context Engine Budget 压力测试。",
    "requirements": requirements,
    "acceptance_criteria": spec_ac_list,
}

arch = {
    "artifact": {"id": "order-architecture", "type": "architecture",
                 "title": "电商订单系统架构（大规模版）", "domain": "order",
                 "status": "reviewed", "version": "1.0.0"},
    "overview": "超大规模订单系统架构，包含 80 个约束和 15 个 ADR。",
    "constraints": constraints,
    "decisions": [
        {"id": f"ADR-{i+1:03d}", "title": f"架构决策 {i+1}",
         "decision": f"采用方案 {i+1}：经过评估 {random.choice(['微服务','单体','事件驱动','CQRS','DDD','分层架构','六边形架构','整洁架构'])} ，"
                     f"决定使用 {random.choice(['Kafka','RabbitMQ','Redis Stream','RocketMQ','Pulsar'])} 作为 {random.choice(['消息队列','缓存','配置中心','服务发现','网关'])}。"
                     f"原因：{random.choice(['高吞吐','低延迟','运维成熟','社区活跃','云原生支持'])}。",
         "status": "accepted",
         "context": f"系统当前面临 {random.choice(CONDS)} 的挑战，需要 {random.choice(QUALITIES)}。",
         "consequences": f"增加系统复杂度但提升{random.choice(['可靠性','可扩展性','可维护性','可观测性'])}。"}
        for i in range(15)
    ]
}

# 写文件
with open(OUT_DIR / "spec-stress.yaml", "w", encoding="utf-8") as f:
    yaml.dump(spec, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)

with open(OUT_DIR / "architecture-stress.yaml", "w", encoding="utf-8") as f:
    yaml.dump(arch, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)

# Task markdown
task_md = f"""---
artifact:
  id: ORD-order-001
  type: task
  title: 订单核心服务实现（大规模版）
  domain: order
  status: active
  version: "1.0.0"
  dependencies: [ORD-specs, order-architecture]
---

# ORD-order-001

## 需求映射

"""
for rid in task_req_refs:
    task_md += f"| {rid} | full |\n"

task_md += "\n## 验证步骤\n\n"
for i, ac_id in enumerate(task_ac_ids):
    task_md += f"### VAL-ORD-001-{i+1:03d}\n**验收标准**：{ac_id}\n**命令**：`pytest -k test_{i+1}`\n\n"

task_md += "\n## 约束引用\n\n"
for cid in task_con_refs:
    task_md += f"- {cid}\n"

with open(OUT_DIR / "task-stress.md", "w", encoding="utf-8") as f:
    f.write(task_md)

# ==================== 统计 ====================
spec_yaml = yaml.dump(spec, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)
arch_yaml = yaml.dump(arch, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)

spec_size = len(spec_yaml.encode("utf-8"))
arch_size = len(arch_yaml.encode("utf-8"))

print(f"Spec: {spec_size:,} bytes (~{spec_size//4:,} tokens)")
print(f"Architecture: {arch_size:,} bytes (~{arch_size//4:,} tokens)")
print(f"References: {len(task_req_refs)} REQ + {len(task_ac_ids)} AC + {len(task_con_refs)} CON = {len(task_req_refs)+len(task_ac_ids)+len(task_con_refs)} total")

# 估算 Context Bundle（只包含引用的部分）
# 粗略假设：引用的 REQ 占 spec 的 80/300 ≈ 27%，但实际内容占比因描述长度而异
est_cb_bytes = spec_size * 0.35 + arch_size * 0.65  # 引用比例估算
est_tokens = est_cb_bytes // 4
print(f"\n估算 Context Bundle: ~{est_cb_bytes:,.0f} bytes (~{est_tokens:,} tokens)")
if est_tokens > 25000:
    print("TRIGGER: Budget exceeded! Will trim P2 first.")
else:
    print("Within budget. Need larger data to trigger trim.")
"""生成 Validation-3 压力测试数据。

场景：大型电商系统（order 域）
- 120 个 Requirement（REQ-ORD-001 ~ REQ-ORD-120）
- 40 个 Architecture Constraint（CON-ORD-001 ~ CON-ORD-040）
- 1 个 Task，引用 30 个 requirement + 20 个 constraint + 15 个 AC

预期：Context Bundle 超过 25000 token 限制，触发 P2 Budget 裁减。
"""

import random
import yaml
from pathlib import Path

OUT_DIR = Path(__file__).parent
random.seed(42)

# 核心业务域：订单系统
DOMAIN = "ORD"

# ==================== 需求模板 ====================
REQ_TEMPLATES = [
    ("订单创建", "用户可以通过前端页面创建新订单，选择商品和数量"),
    ("订单支付", "用户可以通过微信/支付宝完成订单支付"),
    ("支付回调", "支付成功后系统自动更新订单状态为已支付"),
    ("订单取消", "用户可以在支付前取消订单"),
    ("超时取消", "未支付订单 30 分钟后自动取消"),
    ("订单查询", "用户可以按时间范围查询历史订单"),
    ("订单详情", "用户可以查看单个订单的完整信息"),
    ("物流跟踪", "用户可以查看订单的物流配送状态"),
    ("退款申请", "用户可以对已支付订单申请退款"),
    ("退款审核", "管理员可以审核用户的退款申请"),
    ("库存扣减", "下单时自动扣减商品库存"),
    ("库存恢复", "取消订单时自动恢复商品库存"),
    ("优惠券使用", "用户可以在下单时使用优惠券"),
    ("积分抵扣", "用户可以使用积分抵扣订单金额"),
    ("发票开具", "用户可以对已完成订单申请电子发票"),
    ("订单导出", "管理员可以按条件导出订单列表为 CSV"),
    ("批量发货", "管理员可以批量更新订单为已发货"),
    ("收货确认", "用户收到商品后可以确认收货"),
    ("自动确认", "发货后 15 天自动确认收货"),
    ("评价功能", "用户可以对已收货订单进行评价"),
    ("差评处理", "客服可以对差评订单进行跟进处理"),
    ("订单拆分", "多仓库商品自动拆分为子订单"),
    ("合单支付", "多个订单支持合并支付"),
    ("预售订单", "支持预售商品的定金+尾款支付"),
    ("秒杀订单", "秒杀场景下的高并发下单处理"),
    ("拼团订单", "支持拼团模式的订单创建和成团判断"),
    ("跨境订单", "跨境商品的报关信息收集和海关对接"),
    ("货到付款", "支持货到付款的支付方式"),
    ("分期付款", "支持花呗/信用卡分期支付"),
    ("账单分期", "已支付订单支持转为分期"),
]

# 补充到 120 个需求（用变体）
def generate_requirements(count=120):
    reqs = []
    for i in range(count):
        base_idx = i % len(REQ_TEMPLATES)
        variant = i // len(REQ_TEMPLATES)
        title, desc = REQ_TEMPLATES[base_idx]
        if variant > 0:
            title = f"{title}（V{variant+1}）"
            desc = f"{desc}，扩展场景{variant+1}"
        reqs.append({
            "id": f"REQ-{DOMAIN}-{i+1:03d}",
            "title": title,
            "description": desc,
            "priority": random.choice(["must", "should", "could"]),
            "category": random.choice(["functional", "non_functional", "performance"]),
            "scenarios": [
                {
                    "id": f"SC-REQ-{DOMAIN}-{i+1:03d}-01",
                    "given": f"前置条件 {i+1}-A",
                    "when": f"触发动作 {i+1}-A",
                    "then": f"预期结果 {i+1}-A",
                    "acceptance_criteria": [
                        f"验收标准 {i+1}-A1：响应时间 < 500ms",
                        f"验收标准 {i+1}-A2：错误率 < 0.1%"
                    ]
                },
                {
                    "id": f"SC-REQ-{DOMAIN}-{i+1:03d}-02",
                    "given": f"前置条件 {i+1}-B",
                    "when": f"触发动作 {i+1}-B",
                    "then": f"预期结果 {i+1}-B",
                    "acceptance_criteria": [
                        f"验收标准 {i+1}-B1：并发 1000 TPS",
                        f"验收标准 {i+1}-B2：数据一致性保证"
                    ]
                }
            ]
        })
    return reqs

# ==================== 约束模板 ====================
CONSTRAINT_TEMPLATES = [
    ("architecture", "分层约束", "Service 层不得直接访问数据库，必须通过 Repository 接口"),
    ("architecture", "依赖方向", "上层可以依赖下层，下层不得依赖上层"),
    ("security", "认证约束", "所有 API 端点必须通过 JWT Token 认证"),
    ("security", "授权约束", "非管理员用户不得访问管理接口"),
    ("data", "数据一致性", "订单状态变更必须在事务中完成"),
    ("data", "数据隔离", "多租户数据必须通过 tenant_id 隔离"),
    ("reliability", "消息可靠性", "订单事件必须持久化到消息队列后才能确认"),
    ("reliability", "幂等约束", "支付回调接口必须支持幂等处理"),
    ("performance", "响应时间", "订单查询接口 P95 响应时间 < 200ms"),
    ("performance", "并发约束", "下单接口支持 5000 TPS 并发"),
    ("compliance", "日志约束", "所有订单操作必须记录审计日志"),
    ("compliance", "数据保留", "订单数据必须保留至少 5 年"),
    ("testing", "测试覆盖", "Service 层单元测试覆盖率 > 80%"),
    ("testing", "集成测试", "支付流程必须通过集成测试"),
    ("architecture", "接口约束", "所有 Service 方法必须有类型注解"),
    ("security", "输入校验", "所有用户输入必须经过 Pydantic 校验"),
    ("data", "索引约束", "order_id 和 user_id 必须建立联合索引"),
    ("reliability", "超时约束", "外部服务调用超时时间 < 5 秒"),
    ("performance", "缓存约束", "热点商品信息必须缓存，过期时间 10 分钟"),
    ("compliance", "隐私约束", "用户手机号在日志中必须脱敏"),
]

def generate_constraints(count=40):
    cons = []
    for i in range(count):
        base_idx = i % len(CONSTRAINT_TEMPLATES)
        variant = i // len(CONSTRAINT_TEMPLATES)
        c_type, c_title, c_rule = CONSTRAINT_TEMPLATES[base_idx]
        if variant > 0:
            c_title = f"{c_title}（扩展{variant+1}）"
            c_rule = f"{c_rule}，补充规则{variant+1}"
        cons.append({
            "id": f"CON-{DOMAIN}-{i+1:03d}",
            "type": c_type,
            "title": c_title,
            "rule": c_rule,
            "severity": random.choice(["block", "warning", "info"]),
            "verification": random.choice(["code_review", "static_analysis", "automated_test"]),
        })
    return cons

# ==================== 生成数据 ====================

requirements = generate_requirements(120)
constraints = generate_constraints(40)

# Task 引用：30 个 requirement + 15 个 AC + 20 个 constraint
task_requirement_refs = [
    {"requirement_id": f"REQ-{DOMAIN}-{i:03d}", "coverage": random.choice(["full", "partial"])}
    for i in random.sample(range(1, 121), 30)
]
task_ac_ids = [f"AC-{DOMAIN}-{i:03d}" for i in random.sample(range(1, 121), 15)]
task_constraint_refs = [f"CON-{DOMAIN}-{i:03d}" for i in random.sample(range(1, 41), 20)]

# 写 Spec
spec = {
    "artifact": {
        "id": "ORD-specs",
        "type": "spec",
        "title": "电商订单系统规格",
        "domain": "order",
        "status": "reviewed",
        "version": "1.0.0",
    },
    "overview": "大型电商订单系统，支持下单、支付、物流、退款、评价等完整订单生命周期。日订单量 100 万+。",
    "requirements": requirements,
    "acceptance_criteria": [
        {"id": f"AC-ORD-{i+1:03d}", "description": f"全局验收标准 {i+1}：系统在 99.9% 可用性下运行",
         "verification_method": random.choice(["automated_test", "performance_test", "code_review"])}
        for i in range(120)
    ],
    "business_rules": [
        {"id": f"BR-ORD-{i+1:03d}", "description": f"业务规则 {i+1}"}
        for i in range(30)
    ]
}

with open(OUT_DIR / "spec-stress.yaml", "w", encoding="utf-8") as f:
    yaml.dump(spec, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

# 写 Architecture
arch = {
    "artifact": {
        "id": "order-architecture",
        "type": "architecture",
        "title": "电商订单系统架构规格",
        "domain": "order",
        "status": "reviewed",
        "version": "1.0.0",
    },
    "overview": "订单系统采用微服务架构，包含订单服务、支付服务、库存服务、物流服务。服务间通过消息队列异步通信。",
    "constraints": constraints,
    "decisions": [
        {"id": f"ADR-{i+1:03d}", "title": f"架构决策 {i+1}",
         "decision": f"使用方案 {i+1} 解决架构问题 {i+1}",
         "status": "accepted",
         "context": f"决策背景 {i+1}",
         "consequences": f"决策后果 {i+1}"}
        for i in range(15)
    ]
}

with open(OUT_DIR / "architecture-stress.yaml", "w", encoding="utf-8") as f:
    yaml.dump(arch, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

# 写 Task
task_md = f"""---
artifact:
  id: ORD-order-001
  type: task
  title: 订单核心服务实现
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
for ref in task_requirement_refs:
    task_md += f"| {ref['requirement_id']} | {ref['coverage']} |\n"

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
for con_id in task_constraint_refs:
    task_md += f"- {con_id}\n"

task_md += """
## 完成定义

- [ ] 所有实现步骤已完成
- [ ] 所有验证步骤已通过
"""

with open(OUT_DIR / "task-stress.md", "w", encoding="utf-8") as f:
    f.write(task_md)

# ==================== 统计 ====================
spec_bytes = len(yaml.dump(spec, allow_unicode=True))
arch_bytes = len(yaml.dump(arch, allow_unicode=True))
print(f"Spec 文件大小: {spec_bytes:,} 字节 (~{spec_bytes//4:,} tokens)")
print(f"Architecture 文件大小: {arch_bytes:,} 字节 (~{arch_bytes//4:,} tokens)")
print(f"Task 引用: {len(task_requirement_refs)} requirements + {len(task_ac_ids)} ACs + {len(task_constraint_refs)} constraints")
print(f"总引用数: {len(task_requirement_refs) + len(task_ac_ids) + len(task_constraint_refs)}")

# 估算 Context Bundle 大小
est_bundle_bytes = spec_bytes + arch_bytes
est_tokens = est_bundle_bytes // 4
print(f"\n估算 Context Bundle: ~{est_bundle_bytes:,} 字节 (~{est_tokens:,} tokens)")
if est_tokens > 25000:
    print("⚠️ 预计超过 Budget 限制（25,000 tokens），将触发 P2 Budget 裁减")
else:
    print("✅ 预计在 Budget 限制内")
