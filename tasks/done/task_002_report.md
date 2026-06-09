## 🛠️ 开发日志 — 任务单 #2

> 🔧 Codex Engineer (GPT-5.5) 编写

### 📝 开发过程

1. **研究后端保洁 API**：阅读 `cleaning.py` router 和 `cleaning/schemas.py`，确认保洁端可用的 6 个核心端点（list / summary / accept / start / open-door / complete）及其请求响应格式。

2. **扩展类型定义**：在 `types.ts` 中新增 `CleaningTask`（22 字段）、`CleaningProof`、`CleaningSummary` 三个接口，与后端 Pydantic Schema 对齐。

3. **创建 demo 数据**：在 `demo.ts` 中新增 4 条不同状态的任务（pending/accepted/in_progress/completed）和 1 个 summary 统计，覆盖全部页面状态。

4. **创建 cleaner.ts API 客户端**：封装 7 个保洁 API 方法，遵循 `withTenant()` 会话模式。

5. **创建 CleanerLayout.vue**：复用 CustomerLayout 结构，顶部绿色主题（`#4a7c59`）区分保洁身份，底部二 Tab（任务/我的）。一键登录使用 cleaner 角色（nickname: "保洁员_李姐"）。

6. **创建 TasksView.vue**：任务列表 + 5 状态筛选 tabs，任务卡片显示房间名、状态标签、计划时间、结算金额。

7. **创建 TaskDetailView.vue**：任务详情 + 状态时间线 + 条件操作按钮。关键逻辑：
   - `pending` → 显示"接单"
   - `accepted` → 显示"开始任务" + "取消接单"
   - `in_progress` → 显示"保洁开门" + "完成任务"
   - "完成任务"弹出表单（图片URL + 备注），以逗号分隔解析图片URL
   - 每次操作调用对应 API 后重载任务数据

8. **创建 CleanerMeView.vue**：个人中心 + 任务统计（待接单/进行中/已逾期/被投诉），点击退出登录清空 token。

9. **更新路由**：新增 `/cleaner/...` 路由组（3 条路由），与 `/customer`、`/` 三级路由并存。

### 🧠 开发思路与依据

**为什么保洁端只有 3 个视图而非 7 个（顾客端）**

保洁员的业务场景更简单：核心就是"看任务→做任务→交任务"。不需要浏览门店、比较房间、计算价格等流程，因此页面数大幅减少。3 个视图覆盖全部流程：列表（概览）、详情（操作）、我的（统计）。

**为什么 TaskDetailView 不独立加载单个任务**

后端 `/api/v1/cleaning/tasks/{id}` 端点确实存在，但保洁端先加载列表再在内存中查找更高效（减少一次 HTTP 请求），且与无 Token 时的 demo 模式行为一致。

**为什么保洁布局使用绿色而非顾客端的青色**

视觉区分：顾客端品牌色 `#0f6f68`（青），保洁端 `#4a7c59`（绿），商家后台深色侧边栏。三端在同一工程中通过颜色即可区分当前身份。

**状态流转设计的依据**

保洁任务状态机：`pending → accepted → in_progress → completed → reviewed → settled`。前端操作按钮的显示逻辑严格对应这个状态机，每个状态下只显示一个"主操作"按钮，避免保洁员误操作。

### 📊 代码变更清单

| 操作 | 文件路径 | 说明 |
|------|---------|------|
| 新增 | `web/src/core/api/cleaner.ts` | 保洁端 API 封装 (7方法) |
| 新增 | `web/src/layouts/cleaner/CleanerLayout.vue` | 保洁移动布局 (顶栏+底Tab) |
| 新增 | `web/src/modules/cleaner/views/TasksView.vue` | 任务列表 (5状态筛选) |
| 新增 | `web/src/modules/cleaner/views/TaskDetailView.vue` | 任务详情+操作 (6种操作) |
| 新增 | `web/src/modules/cleaner/views/CleanerMeView.vue` | 个人中心+统计 |
| 修改 | `web/src/core/api/types.ts` | +28行：CleaningTask/CleaningProof/CleaningSummary |
| 修改 | `web/src/core/api/demo.ts` | +75行：4条保洁任务+demo统计 |
| 修改 | `web/src/app/router/index.ts` | +22行：3条保洁路由 |

### 💡 核心代码解读

#### 关键代码块 1：TaskDetailView 的操作按钮条件渲染

```typescript
const canAccept = computed(() => task.value?.status === "pending");
const canUnaccept = computed(() => task.value?.status === "accepted");
const canStart = computed(() => task.value?.status === "accepted");
const canOpenDoor = computed(() => task.value?.status === "in_progress");
const canComplete = computed(() => task.value?.status === "in_progress");
```

**解读**：每个操作按钮的显示条件由任务当前状态决定。使用 computed 属性实现响应式条件渲染。状态机逻辑：pending 下只能接单 → accepted 下可开始或取消 → in_progress 下可开门或完成。每步操作调用 API 后通过 `await load()` 重新获取任务数据，状态自动更新。

**为什么用多个 computed 而非 switch-case**：Vue 模板中每个按钮独立绑定 `v-if`，多个 computed 比 switch-case 更清晰直观。每个条件单独命名也便于理解业务规则。

#### 关键代码块 2：完成任务的图片URL解析

```typescript
const urls = imageUrlInput.value
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
if (urls.length === 0) {
  actionMsg.value = "请至少输入一张图片URL";
  return;
}
```

**解读**：保洁员通过逗号分隔输入多个图片URL（实际产品中应用文件上传组件替代）。解析逻辑：split → trim → filter 空值。至少一个有效URL才允许提交。`actionLoading.value = false` 提前 return 确保按钮不会卡死在 loading 状态。

**为什么用 URL 输入而非文件上传**：当前项目无对象存储上传组件，URL 输入是 MVP 阶段的简化方案。后端 `image_urls: list[str]` 字段接受 URL 列表，后续可升级为文件上传 + 自动生成 URL。

### ⚠️ 遇到的问题与解决方案

| 问题 | 原因 | 解决方案 | 是否完全解决 |
|------|------|---------|------------|
| `compute` import 位置错误 | `import { computed }` 放在 script setup 底部而非顶部 | 移到顶部与其他 imports 一起 | ✅ |
| CleanerMeView 中 `computed` 未导入 | 遗漏了 import 语句 | 添加 `import { computed } from "vue"` | ✅ |
| 保洁顶栏颜色统一性 | 顾客端和保洁端复用同一 CSS 类名但需要不同主题色 | 在 scoped style 中直接覆盖 `background` 值 | ✅ |

### 📚 参考来源
- 顾客端代码：`web/src/layouts/customer/CustomerLayout.vue`、`web/src/modules/customer/views/*.vue`
- 后端保洁 API：`app/api/v1/routers/cleaning.py`、`app/modules/cleaning/schemas.py`
- BMAD PRD M6 保洁闭环：`python_24_qipaishi/docs/18-m6-cleaning-completion-verification-report.md`
