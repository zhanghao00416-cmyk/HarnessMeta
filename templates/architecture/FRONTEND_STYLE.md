# 前端规范

> 由 harness-specify-arch 根据 project.yaml 的 frontend 段和 constitution 自动生成。
> 本文档是所有前端代码的权威规范，代码实现必须与此保持一致。

## 概述

本文档定义 {{project_name}} 的前端技术栈、目录结构、编码规范和开发约定。

| 技术领域 | 选型 | 版本约束 |
|----------|------|----------|
| 框架 | {{framework}} | {{framework_version}} |
| 构建工具 | {{build_tool}} | {{build_tool_version}} |
| 样式方案 | {{style_solution}} | {{style_version}} |
| 状态管理 | {{state_management}} | {{state_version}} |
| 路由 | {{router}} | {{router_version}} |
| HTTP 客户端 | {{http_client}} | {{http_version}} |
| 测试框架 | {{test_framework}} | {{test_version}} |

---

## 目录结构

```
{{frontend_root}}/
├── public/                      # 静态资源（不经过构建）
├── src/
│   ├── main.{ts,js}             # 应用入口
│   ├── App.{vue,tsx,jsx}        # 根组件
│   ├── router/                  # 路由配置
│   │   └── index.{ts,js}
│   ├── stores/                  # 状态管理（Pinia/Vuex/Redux/Zustand）
│   │   └── {{store_files}}
│   ├── views/                   # 页面级组件（按业务域分组）
│   │   └── {{domain}}/
│   │       └── {{view_component}}.vue
│   ├── components/              # 可复用组件
│   │   ├── common/              # 全项目通用（Button, Modal, Table 等）
│   │   └── {{domain}}/          # 业务域专用
│   ├── composables/             # 组合式函数（Vue）/ Hooks（React）
│   │   └── {{composable_name}}.ts
│   ├── services/                # API 调用层（与后端 API_CONTRACT 对应）
│   │   └── {{service_name}}.ts
│   ├── utils/                   # 工具函数
│   │   └── {{util_name}}.ts
│   ├── types/                   # 全局类型定义
│   │   └── {{type_name}}.ts
│   ├── assets/                  # 样式、图片、字体（经过构建）
│   │   ├── styles/
│   │   ├── images/
│   │   └── fonts/
│   └── directives/              # 自定义指令（如适用）
│       └── {{directive_name}}.ts
├── tests/                       # 测试文件（或 __tests__ 目录）
├── index.html
├── package.json
├── {{config_files}}
└── Dockerfile                   # 前端镜像构建（如适用）
```

---

## 命名规范

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `UserProfile.vue`, `DataTable.tsx` |
| 组合式函数/Hook | camelCase，前缀 `use` | `useAuth.ts`, `usePagination.ts` |
| 工具函数 | camelCase | `formatDate.ts`, `debounce.ts` |
| 常量/配置 | UPPER_SNAKE_CASE 或 camelCase | `API_CONFIG.ts`, `themeConfig.ts` |
| 样式文件 | 与组件同名或 kebab-case | `UserProfile.scss`, `global-styles.css` |
| 测试文件 | 与被测文件同名 + `.test` 后缀 | `UserProfile.test.ts` |

### 组件命名

- **单文件组件**：PascalCase，多词组合避免与 HTML 元素冲突
  - ✅ `UserCard`, `SearchInput`
  - ❌ `user-card`, `button`
- **组件引用**：模板中使用 PascalCase，属性中使用 kebab-case
  - ✅ `<UserCard :user-name="name" />`

---

## 组件规范

### 组件结构（Vue 示例）

```vue
<script setup lang="ts">
// 1. 导入（按类型分组：Vue API → 第三方 → 内部）
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import UserAvatar from '@/components/common/UserAvatar.vue'

// 2. 类型/接口定义
interface Props {
  userId: string
  editable?: boolean
}

// 3. Props / Emits 定义
const props = withDefaults(defineProps<Props>(), {
  editable: false
})

const emit = defineEmits<{
  (e: 'update', userId: string, data: UserData): void
  (e: 'delete', userId: string): void
}>()

// 4. 组合式函数调用
const route = useRoute()
const userStore = useUserStore()

// 5. 响应式状态
const loading = ref(false)
const userData = ref<UserData | null>(null)

// 6. 计算属性
const displayName = computed(() => {
  return userData.value?.nickname || userData.value?.username || '未知用户'
})

// 7. 方法
async function fetchUser() {
  loading.value = true
  try {
    userData.value = await userStore.fetchById(props.userId)
  } finally {
    loading.value = false
  }
}

// 8. 生命周期
onMounted(fetchUser)
</script>

<template>
  <!-- 模板内容 -->
</template>

<style scoped lang="scss">
/* 样式内容 */
</style>
```

### 组件设计原则

1. **单一职责**：每个组件只做一件事，复杂页面拆分为容器组件 + 展示组件
2. **Props 向下，Events 向上**：数据流单向，避免子组件直接修改父组件状态
3. **逻辑复用优先用组合式函数**：避免 Mixin，优先使用 Composables/Hooks
4. **样式隔离**：组件样式使用 `scoped` 或 CSS Modules，禁止全局样式污染

---

## API 调用层规范

### 服务层结构

```typescript
// src/services/user.ts
import { apiClient } from '@/utils/apiClient'
import type { User, UserCreateDTO } from '@/types/user'

export async function getUser(id: string): Promise<User> {
  const response = await apiClient.get(`/users/${id}`)
  return response.data
}

export async function createUser(data: UserCreateDTO): Promise<User> {
  const response = await apiClient.post('/users', data)
  return response.data
}
```

### 规范要求

- **与 API_CONTRACT 一一对应**：每个后端端点必须有一个前端 service 函数
- **统一错误处理**：service 层拦截 HTTP 错误，转换为业务错误抛出
- **类型安全**：所有请求参数和响应必须定义 TypeScript 类型
- **禁止在组件中直接调用 fetch/axios**：必须通过 service 层

---

## 状态管理规范

### 存储结构

```
stores/
├── auth.ts              # 认证状态（用户、Token、权限）
├── user.ts              # 用户数据（CRUD 操作）
├── {{domain}}.ts        # 业务域状态
└── app.ts               # 应用级状态（主题、语言、加载状态）
```

### 规范要求

- **按业务域拆分 Store**：禁止单个巨型 Store
- **Actions 处理异步**：Mutations/State 只处理同步数据变更
- **Getter 用于派生状态**：避免在组件中重复计算
- **持久化状态显式声明**：哪些状态需要 localStorage/sessionStorage 必须文档化

---

## 路由规范

### 路由配置

```typescript
// src/router/index.ts
const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users/:id',
    name: 'UserDetail',
    component: () => import('@/views/user/UserDetail.vue'),
    props: true
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]
```

### 规范要求

- **路由懒加载**：所有页面级组件使用 `() => import()`
- **路由名称唯一**：每个路由必须有 `name`，用于导航和权限控制
- **Meta 字段标准化**：`requiresAuth`, `roles`, `title`, `layout`
- **嵌套路由反映页面结构**：父子关系对应布局嵌套

---

## 样式规范

### 样式方案

| 方案 | 适用场景 | 示例 |
|------|----------|------|
| **Scoped CSS** | 组件级样式 | Vue `<style scoped>` |
| **CSS Modules** | 需要类名映射 | React `styles.module.css` |
| **预处理器** | 复杂样式逻辑 | SCSS / Less |
| **CSS-in-JS** | 动态样式 | Styled Components / Emotion |
| **原子类** | 快速布局 | Tailwind CSS |

### 规范要求

- **变量集中管理**：颜色、间距、字体大小使用 CSS 变量或主题配置
- **禁止魔法数字**：`margin: 16px` → `margin: var(--spacing-md)`
- **响应式断点统一**：使用预定义断点（sm: 640px, md: 768px, lg: 1024px, xl: 1280px）
- **z-index 分层管理**：定义层级系统（tooltip > modal > dropdown > header > content）

---

## 测试规范

### 测试层级

| 层级 | 范围 | 工具 | 覆盖率要求 |
|------|------|------|-----------|
| 单元测试 | 组件、组合式函数、工具 | Vitest / Jest | 70% |
| 集成测试 | 组件交互、Store 逻辑 | Vitest / Testing Library | 50% |
| E2E 测试 | 完整用户流程 | Playwright / Cypress | 核心流程 |

### 测试文件位置

- 与源码并列：`Component.test.ts` 放在 `Component.vue` 同级目录
- 或集中管理：`tests/unit/` 和 `tests/e2e/`

---

## 构建与部署

### 环境变量

| 变量 | 用途 | 示例 |
|------|------|------|
| `VITE_API_BASE_URL` | 后端 API 地址 | `https://api.example.com` |
| `VITE_APP_TITLE` | 应用标题 | `My App` |
| `VITE_APP_VERSION` | 应用版本 | `1.0.0` |

> 所有环境变量必须以 `VITE_` 开头（Vite）或按构建工具要求命名。

### 构建输出

- 生产构建输出到 `dist/` 目录
- 静态资源使用 CDN 时，配置 publicPath 或 base URL
- 启用 gzip/brotli 压缩

---

## 变更规则

1. **技术栈变更必须更新本文档**：框架、构建工具、状态管理方案变更时同步更新
2. **新增组件类型需注册**：在 COMPONENT_LIBRARY.md 中登记新组件
3. **API 变更同步**：后端 API_CONTRACT 变更时，前端 service 层必须同步更新
4. **样式变量变更全局评估**：修改主题变量可能影响全项目，需评估影响范围
5. **变更后同步更新 `docs/meta/FACT_REGISTRY.md` 的前端配置条目
