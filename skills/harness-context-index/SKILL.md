---
name: harness-context-index
description: 构建和维护项目上下文索引。扫描项目结构，生成可复用的元数据索引文件，供其他 Skill 和 Agent 快速定位文件和理解项目结构。只读，不修改代码。
---

# harness-context-index：项目上下文索引

## 触发条件

以下场景执行：

1. **已有代码接入后**：`harness-adopt-scan` 完成后，执行本 Skill 生成索引
2. **项目结构变化后**：新增/删除/重命名模块后，索引已过时
3. **探索前**：`harness-explore` 执行前，确保索引最新以快速定位文件
4. **用户主动要求**：用户说"生成项目索引"或"更新索引"

## 输入

- 项目根目录（当前工作目录）
- `project.yaml`（必须存在）
- `docs/specs/`（可选，用于域映射）
- `ARCHITECTURE.md`（可选，用于理解目录约定）

## 输出

生成以下索引文件（存入 `docs/meta/`）：

| 文件 | 内容 | 用途 |
|------|------|------|
| `docs/meta/project-index.yaml` | 所有源文件的路径、域、类型 | 快速文件定位 |
| `docs/meta/domain-map.yaml` | 业务域与代码路径、规格文档的映射 | 理解模块划分 |
| `docs/meta/dependency-map.yaml` | 文件间的 import/引用关系 | 影响范围分析 |

更新：
- `progress.md`：记录索引生成状态

---

## 步骤

### 1. 扫描项目结构

递归扫描源代码目录，识别以下目录：

```
backend/
frontend/
services/
apps/
src/
lib/
app/
```

**忽略目录**：

```
venv/
node_modules/
dist/
build/
__pycache__/
.git/
.harness/
```

收集每个源文件：
- `path`：相对路径
- `extension`：文件扩展名
- `directory`：所在目录

### 2. 构建项目索引（project-index.yaml）

为每个源文件确定类型：

| 类型 | 判断依据 |
|------|----------|
| `api` | 路由定义、接口声明、控制器方法 |
| `service` | 业务逻辑、服务层、use case |
| `repository` | 数据访问、DAO、存储库 |
| `model` | 数据模型、实体定义、ORM |
| `schema` | 序列化器、DTO、验证模式 |
| `controller` | HTTP 控制器、请求处理器 |
| `component` | UI 组件、可复用视图 |
| `page` | 页面级组件、路由视图 |
| `utility` | 工具函数、辅助类 |
| `config` | 配置文件、常量定义 |
| `test` | 测试文件、mock 数据 |
| `other` | 不符合以上类型的文件 |

**确定 domain**：
- 从文件路径推断（如 `src/auth/` → domain: `auth`）
- 从 `docs/specs/` 目录结构交叉验证
- 无法确定时标记为 `unknown`

生成 `project-index.yaml`：

```yaml
meta:
  generated_at: "2024-01-15T10:30:00Z"
  total_files: 128
  version: 1

files:
  - path: src/auth/controller.py
    domain: auth
    type: controller
    extension: .py
    directory: src/auth
  - path: src/auth/service.py
    domain: auth
    type: service
    extension: .py
    directory: src/auth
  - path: frontend/pages/login.vue
    domain: auth
    type: page
    extension: .vue
    directory: frontend/pages
```

### 3. 构建域映射（domain-map.yaml）

识别业务域，来源：
- `docs/specs/` 下的子目录名
- 源代码目录结构（如 `src/auth/`、`src/user/`）
- `project.yaml` 中的 `features` 列表

生成 `domain-map.yaml`：

```yaml
meta:
  generated_at: "2024-01-15T10:30:00Z"
  total_domains: 5

domains:
  auth:
    specs:
      - docs/specs/auth/spec.md
    paths:
      - src/auth
      - frontend/pages/auth
    description: "用户认证与授权"
    
  user:
    specs:
      - docs/specs/user/spec.md
    paths:
      - src/user
      - frontend/pages/user
    description: "用户管理"
```

### 4. 构建依赖图（dependency-map.yaml）

分析文件间的 import/引用关系：

**Python**：
```python
from app.user.service import UserService
```
→ 记录 `src/auth/controller.py` 依赖 `src/user/service.py`

**TypeScript/JavaScript**：
```typescript
import UserService from "../user/service"
```
→ 记录 `frontend/pages/login.vue` 依赖 `frontend/services/user.ts`

**Go**：
```go
import "github.com/project/user/service"
```
→ 记录 `backend/auth/handler.go` 依赖 `backend/user/service.go`

生成 `dependency-map.yaml`：

```yaml
meta:
  generated_at: "2024-01-15T10:30:00Z"
  total_dependencies: 64

dependencies:
  src/auth/controller.py:
    imports:
      - src/auth/service.py
      - src/user/service.py
      - src/common/response.py
    imported_by:
      - src/auth/routes.py
      
  src/user/service.py:
    imports:
      - src/user/repository.py
      - src/common/exceptions.py
    imported_by:
      - src/auth/controller.py
      - src/admin/controller.py
```

### 5. 一致性检查

验证索引完整性：

- [ ] `project-index.yaml` 中所有文件路径真实存在
- [ ] `domain-map.yaml` 中所有 specs 路径真实存在（如声明了 specs）
- [ ] `dependency-map.yaml` 中所有 import 目标在 `project-index.yaml` 中存在
- [ ] `domain-map.yaml` 中所有 paths 在 `project-index.yaml` 中有对应文件

发现无效条目时，在报告中标注但不阻塞生成。

### 6. 更新进度

更新 `progress.md`：

```yaml
context_index:
  generated_at: "2024-01-15T10:30:00Z"
  files: 128
  domains: 5
  dependencies: 64
  status: success
```

---

## 约束

- **只读**：禁止修改任何源代码文件
- **不生成代码**：仅生成元数据索引
- **增量更新**：如索引已存在，对比差异后更新（而非全量重建）
- **路径相对化**：所有路径使用相对路径（相对于项目根目录）
- **可跳过**：上下文不足时，可生成简化版索引（仅 project-index.yaml）

---

## 验证清单

执行完成后自检：

- [ ] `docs/meta/project-index.yaml` 已生成
- [ ] `docs/meta/domain-map.yaml` 已生成
- [ ] `docs/meta/dependency-map.yaml` 已生成
- [ ] 所有索引文件中的路径真实存在（或已标注无效）
- [ ] `progress.md` 已更新索引状态

---

## 返回格式

```markdown
## 项目索引生成完成

- 扫描文件：{{total_files}} 个
- 识别域：{{total_domains}} 个
- 分析依赖：{{total_dependencies}} 条
- 生成文件：
  - docs/meta/project-index.yaml
  - docs/meta/domain-map.yaml
  - docs/meta/dependency-map.yaml

### 统计
| 类型 | 数量 |
|------|------|
| api | {{N}} |
| service | {{N}} |
| controller | {{N}} |
| model | {{N}} |
| component | {{N}} |
| page | {{N}} |
| utility | {{N}} |
| test | {{N}} |
| other | {{N}} |

### 注意事项
- {{note_1}}
- {{note_2}}
```
