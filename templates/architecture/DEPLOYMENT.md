# 部署架构

> 由 harness-specify-arch 根据 project.yaml 的 deployment 段和 constitution 自动生成。
> 本文档是所有部署配置和容器编排的权威来源。

## 概述

本文档定义 {{project_name}} 的部署架构，包括容器编排、服务依赖和运行环境配置。

| 部署方式 | 配置文件 | 说明 |
|----------|---------|------|
| {{deployment_type}} | {{compose_file}} | {{deployment_description}} |

---

## 服务拓扑

```
{{service_topology_diagram}}
```

---

## 服务注册表

> 列出 docker-compose 中编排的所有服务。

| 服务名 | 镜像/构建 | 端口映射 | 依赖 | 用途 |
|--------|----------|---------|------|------|
| {{service_name}} | {{image_or_build}} | {{port_mapping}} | {{depends_on}} | {{purpose}} |

---

## Dockerfile 规范

> 应用镜像的构建规范，由工单实现时必须遵守。

### 基础镜像

```dockerfile
{{dockerfile_base_image}}
```

### 构建阶段

| 阶段 | 说明 | 关键指令 |
|------|------|---------|
| {{stage_name}} | {{stage_description}} | {{key_instructions}} |

### 镜像约束

1. 生产镜像禁止包含开发工具（编译器、调试器、测试框架）
2. 敏感信息（API Key、数据库密码）禁止写入镜像，必须通过环境变量注入
3. 镜像体积应控制在合理范围内，使用多阶段构建减小最终镜像

---

## 环境变量映射

> 列出所有通过环境变量注入的配置项，与 `project.yaml` context 段和 `ARCHITECTURE.md` 命名约定保持一致。

| 环境变量 | 用途 | 默认值 | 必填 |
|----------|------|--------|------|
| {{env_var}} | {{purpose}} | {{default_value}} | {{required}} |

---

## 健康检查

> 每个服务的存活探针和就绪探针配置。

| 服务 | 检查类型 | 端点/命令 | 间隔 | 超时 | 失败阈值 |
|------|---------|---------|------|------|---------|
| {{service_name}} | HTTP / CMD | {{check_endpoint}} | {{interval}} | {{timeout}} | {{retries}} |

---

## 网络与存储

### 网络配置

| 网络名 | 类型 | 连接服务 | 说明 |
|--------|------|---------|------|
| {{network_name}} | {{network_type}} | {{connected_services}} | {{purpose}} |

### 持久化卷

| 卷名 | 挂载路径 | 用途 |
|------|---------|------|
| {{volume_name}} | {{mount_path}} | {{purpose}} |

---

## 构建与发布命令

| 命令 | 用途 |
|------|------|
| `docker compose build` | 构建所有服务镜像 |
| `docker compose up -d` | 后台启动所有服务 |
| `docker compose down` | 停止并移除所有服务 |
| `docker compose logs -f {{service_name}}` | 查看指定服务日志 |
| `{{custom_command}}` | {{custom_purpose}} |

---

## 变更规则

1. 新增服务或修改端口映射时，必须先更新本文档，再修改 `docker-compose.yml`
2. 新增环境变量时必须同步本文档和 `ARCHITECTURE.md` 的配置段
3. 部署架构变更需评估对所有运行中服务的影响
4. 变更后同步更新 `docs/meta/FACT_REGISTRY.md` 的部署配置条目
