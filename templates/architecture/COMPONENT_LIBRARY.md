# 组件库

> 由 harness-specify-arch 根据 project.yaml 的 features 和 constitution 自动生成。
> 本文档是所有可复用组件的注册表，新增组件必须先在此登记。

## 概述

本文档定义 {{project_name}} 的组件体系，包括通用组件、业务组件和第三方组件集成。

| 类别 | 说明 | 位置 |
|------|------|------|
| **通用组件** | 全项目复用的基础 UI 元素 | `src/components/common/` |
| **业务组件** | 特定业务域的复合组件 | `src/components/{{domain}}/` |
| **布局组件** | 页面骨架、导航、侧边栏 | `src/components/layout/` |
| **第三方组件** | 外部库组件的封装或直接使用 | 按库分类 |

---

## 通用组件注册表

> 基础 UI 组件，所有业务组件和页面均可使用。

### 基础组件

| 组件名 | 用途 | Props | Events | 状态 |
|--------|------|-------|--------|------|
| **BaseButton** | 按钮 | `variant`, `size`, `loading`, `disabled` | `click` | [TBD: filled by Fxx] |
| **BaseInput** | 文本输入 | `modelValue`, `type`, `placeholder`, `error` | `update:modelValue`, `blur` | [TBD: filled by Fxx] |
| **BaseSelect** | 下拉选择 | `modelValue`, `options`, `multiple` | `update:modelValue` | [TBD: filled by Fxx] |
| **BaseModal** | 模态框 | `visible`, `title`, `width`, `closable` | `update:visible`, `confirm`, `cancel` | [TBD: filled by Fxx] |
| **BaseTable** | 数据表格 | `data`, `columns`, `loading`, `pagination` | `row-click`, `sort-change`, `page-change` | [TBD: filled by Fxx] |
| **BasePagination** | 分页器 | `current`, `total`, `pageSize` | `change` | [TBD: filled by Fxx] |
| **BaseLoading** | 加载状态 | `type`, `text` | - | [TBD: filled by Fxx] |
| **BaseEmpty** | 空状态 | `description`, `image` | - | [TBD: filled by Fxx] |
| **BaseTooltip** | 文字提示 | `content`, `placement` | - | [TBD: filled by Fxx] |
| **BaseBadge** | 徽标 | `count`, `max`, `status` | - | [TBD: filled by Fxx] |

### 表单组件

| 组件名 | 用途 | Props | Events | 状态 |
|--------|------|-------|--------|------|
| **FormInput** | 表单输入（带标签和校验） | `label`, `rules`, `modelValue` | `update:modelValue` | [TBD: filled by Fxx] |
| **FormSelect** | 表单选择（带标签和校验） | `label`, `rules`, `options` | `update:modelValue` | [TBD: filled by Fxx] |
| **FormDatePicker** | 日期选择 | `label`, `rules`, `format` | `update:modelValue` | [TBD: filled by Fxx] |
| **FormUpload** | 文件上传 | `label`, `rules`, `accept`, `maxSize` | `update:modelValue`, `upload` | [TBD: filled by Fxx] |
| **FormRichText** | 富文本编辑器 | `label`, `rules`, `modelValue` | `update:modelValue` | [TBD: filled by Fxx] |

### 反馈组件

| 组件名 | 用途 | 触发方式 | 状态 |
|--------|------|----------|------|
| **Toast** | 轻量提示 | `toast.success(message)`, `toast.error(message)` | [TBD: filled by Fxx] |
| **Dialog** | 确认对话框 | `dialog.confirm(options)` | [TBD: filled by Fxx] |
| **Notification** | 通知消息 | `notification.info(options)` | [TBD: filled by Fxx] |
| **ProgressBar** | 进度条 | 全局或局部 | [TBD: filled by Fxx] |

---

## 布局组件注册表

| 组件名 | 用途 | 插槽 | 状态 |
|--------|------|------|------|
| **AppLayout** | 应用整体布局（侧边栏 + 头部 + 内容区） | `sidebar`, `header`, `content` | [TBD: filled by Fxx] |
| **Sidebar** | 侧边导航菜单 | `logo`, `menu`, `footer` | [TBD: filled by Fxx] |
| **TopHeader** | 顶部导航栏 | `logo`, `nav`, `actions` | [TBD: filled by Fxx] |
| **PageContainer** | 页面内容容器（面包屑 + 标题 + 操作区） | `breadcrumb`, `title`, `actions`, `default` | [TBD: filled by Fxx] |
| **Card** | 卡片容器 | `title`, `extra`, `default`, `footer` | [TBD: filled by Fxx] |
| **SplitPane** | 分割面板（左右/上下） | `left`, `right` / `top`, `bottom` | [TBD: filled by Fxx] |

---

## 业务组件注册表

> 按业务域分组，每个域的组件只在该域的页面中使用。

### {{domain_name}} — [TBD: filled by Fxx]

| 组件名 | 用途 | 依赖通用组件 | 状态 |
|--------|------|-------------|------|
| **{{component_name}}** | {{description}} | {{dependencies}} | [TBD: filled by Fxx] |

---

## 第三方组件集成

> 外部 UI 库或工具组件的集成方式。

| 库名 | 用途 | 集成方式 | 版本 | 状态 |
|------|------|----------|------|------|
| **{{library_name}}** | {{purpose}} | 全局引入 / 按需引入 / 组件封装 | {{version}} | [TBD: filled by Fxx] |

### 集成规范

- **全局引入**：适用于整个项目都需要的库（如图标库、工具库）
- **按需引入**：适用于大型组件库（如 Element Plus、Ant Design Vue），使用自动导入插件
- **组件封装**：适用于需要统一行为或样式的第三方组件，封装为项目内部组件

---

## 组件开发规范

### 新增组件流程

1. **需求评估**：确认是通用组件还是业务组件
2. **命名注册**：在本文档对应表格中登记组件名、用途、Props、Events
3. **设计文档**：复杂组件先写设计说明（状态机、数据流、边界情况）
4. **实现开发**：遵循 FRONTEND_STYLE.md 的编码规范
5. **测试覆盖**：单元测试覆盖 Props 校验、Events 触发、边界状态
6. **文档更新**：更新本文档的"状态"列为"已完成"

### 组件设计检查清单

- [ ] Props 有完整类型定义和默认值
- [ ] Events 有完整类型定义和文档
- [ ] 支持 `v-model` 或等效双向绑定（如适用）
- [ ] 支持插槽自定义（如适用）
- [ ] 有 loading / empty / error 状态
- [ ] 响应式适配（移动端 / 平板 / 桌面）
- [ ] 键盘可访问（Tab 导航、Enter 触发）
- [ ] 屏幕阅读器友好（ARIA 属性）

---

## 变更规则

1. **新增组件必须先注册**：禁止未在本文档登记的组件进入代码库
2. **组件废弃需标记**：状态改为"已废弃"，注明替代组件和废弃日期
3. **Props 变更需评估**：修改 Props 接口可能影响所有调用方
4. **通用组件升级全局测试**：修改通用组件后需运行全项目测试
5. **变更后同步更新 `docs/meta/FACT_REGISTRY.md` 的组件条目
