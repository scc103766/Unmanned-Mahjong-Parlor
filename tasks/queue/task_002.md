# 任务单 #2

**任务名称**：M8 保洁移动网页 — 保洁任务闭环
**优先级**：P0
**依赖**：后端保洁 API 已完成 (M6)

---

## 任务描述

在 `web/` 工程中新增保洁移动网页，实现保洁员核心业务流程：查看任务列表 → 接单 → 开始任务 → 开门清洁 → 上传凭证 → 完成。

---

## 开发思路与依据（必读）

### 为什么这样做

保洁端是三端闭环（顾客/商家/保洁）的最后一端。后端 M6 已完成完整的保洁 API（12个端点），前端只需按移动 H5 模式接入。保洁端页面数少（3个视图），但涉及状态流转和开门授权，需重点关注状态机显示和操作按钮的条件渲染。

### 技术选型依据

- **复用 CustomerLayout 模式**：顶栏 + 底Tab 结构，`max-width: 480px` 移动视口，与顾客端一致
- **API 封装模式**：沿用 `apiGet`/`apiPost`，新增 `cleanerApi` 对象
- **状态管理**：每页面独立 `loading`/`error`/`data`，路由 query 传 taskId

### 与其他模块的关系

- 共享 session store（Pinia），cleaner 角色通过 dev-bootstrap 登录
- 与顾客端共享 API client 基础设施（`apiGet`/`apiPost`/`unwrap`）
- 任务完成后房间清洁状态更新，影响顾客端的房间可用性展示

---

## 后端 API 速查

保洁端需要使用的后端接口：

```
GET    /api/v1/cleaning/tasks          — 任务列表 (支持 status filter)
GET    /api/v1/cleaning/summary        — 任务摘要统计
POST   /api/v1/cleaning/tasks/{id}/accept    — 接单
POST   /api/v1/cleaning/tasks/{id}/start     — 开始任务
POST   /api/v1/cleaning/tasks/{id}/open-door — 保洁开门
POST   /api/v1/cleaning/tasks/{id}/complete  — 完成任务（上传凭证）
```

后端 CleaningTaskResponse 关键字段：
- `id`, `store_id`, `room_id`, `order_id`
- `status`: pending/assigned/accepted/in_progress/pending_review/completed/cancelled/rejected/settled
- `cleaner_id`, `scheduled_start_at`, `scheduled_end_at`
- `accepted_at`, `started_at`, `completed_at`
- `settlement_amount`
- `review_note`, `cancel_reason`, `complaint_reason`

---

## 输出要求

### 1. 新增文件

#### 1.1 `src/core/api/cleaner.ts` — 保洁端 API 封装

```typescript
export const cleanerApi = {
  listTasks(params?)          → GET /api/v1/cleaning/tasks
  getSummary()                → GET /api/v1/cleaning/summary
  acceptTask(taskId)          → POST /api/v1/cleaning/tasks/{taskId}/accept
  startTask(taskId)           → POST /api/v1/cleaning/tasks/{taskId}/start
  openTaskDoor(taskId)        → POST /api/v1/cleaning/tasks/{taskId}/open-door
  completeTask(taskId, body)  → POST /api/v1/cleaning/tasks/{taskId}/complete
}
```

#### 1.2 `src/layouts/cleaner/CleanerLayout.vue`

参考 `CustomerLayout.vue` 结构：
- 顶栏：标题 + 一键登录（cleaner 角色）
- 底部三 Tab：📋 任务 / 📊 统计 / 👤 我的
- `max-width: 480px; margin: 0 auto;`

#### 1.3 `src/modules/cleaner/views/TasksView.vue` — 任务列表

- 顶部状态筛选 tabs：全部 / 待接单 / 已接单 / 进行中 / 已完成
- 任务卡片：房间名、门店名、状态标签、金额、时间
- 点击跳转 TaskDetailView（传 taskId）
- 无 Token 时使用 demo 数据

#### 1.4 `src/modules/cleaner/views/TaskDetailView.vue` — 任务详情

- 展示任务完整信息：门店、房间、订单号、状态、金额
- 状态标签（与商家后台一致的 statusLabel/statusTone）
- 根据状态显示操作按钮：
  - pending → "接单"按钮
  - accepted → "开始任务"按钮 + "取消接单"
  - in_progress → "开门"按钮 + "完成任务"按钮
  - completed → 显示凭证图片（URL列表）
- 完成时输入框：图片URL（逗号分隔） + 备注
- 每次操作调用对应 API，展示结果 toast/notice

#### 1.5 `src/modules/cleaner/views/CleanerMeView.vue` — 个人中心

- 显示登录状态和角色信息
- 任务摘要统计（调用 `/cleaning/summary`）
- 退出登录按钮

### 2. 修改文件

#### 2.1 `src/app/router/index.ts`

新增 cleaner 路由组：

```typescript
{
  path: "/cleaner",
  component: () => import("@/layouts/cleaner/CleanerLayout.vue"),
  redirect: { name: "cleaner-tasks" },
  children: [
    { path: "tasks", name: "cleaner-tasks", component: ..., meta: { title: "保洁任务", roles: ["cleaner"] } },
    { path: "tasks/:taskId", name: "cleaner-task-detail", component: ..., meta: { title: "任务详情", roles: ["cleaner"] } },
    { path: "me", name: "cleaner-me", component: ..., meta: { title: "我的", roles: [] } },
  ],
},
```

#### 2.2 `src/core/api/types.ts` — 补充保洁类型

```typescript
export interface CleaningTask {
  id: string; tenant_id: string; store_id: string; room_id: string;
  order_id: string; cleaner_id?: string | null; status: string;
  scheduled_start_at?: string | null; scheduled_end_at?: string | null;
  accepted_at?: string | null; started_at?: string | null;
  completed_at?: string | null; reviewed_at?: string | null;
  settled_at?: string | null; canceled_at?: string | null;
  review_note?: string | null; cancel_reason?: string | null;
  complaint_reason?: string | null; complained_at?: string | null;
  settlement_amount: MoneyLike; created_at?: string | null;
}

export interface CleaningProof {
  id: string; tenant_id: string; task_id: string;
  uploaded_by: string; image_urls: string[];
  remark?: string | null; created_at?: string | null;
}

export interface CleaningSummary {
  pending_count: number; overdue_count: number;
  in_progress_count: number; complained_count: number;
  overdue_task_ids: string[];
}
```

#### 2.3 `src/core/api/demo.ts` — 补充保洁 demo 数据

至少包含 4 条不同状态的任务数据（pending/accepted/in_progress/completed）。

### 3. `src/core/api/demo.ts` 补充

```typescript
export const demoCleaningTasks: CleaningTask[] = [
  { id: "task_demo_1", ..., status: "pending", settlement_amount: "30.00" },
  { id: "task_demo_2", ..., status: "in_progress", settlement_amount: "25.00" },
  { id: "task_demo_3", ..., status: "completed", settlement_amount: "28.00" },
  { id: "task_demo_4", ..., status: "pending", settlement_amount: "22.00" },
];
```

---

## 验收标准

1. ✅ `npm run build` 构建通过，无新增 TypeScript 错误
2. ✅ 无 Token 时，保洁页面展示 demo 数据
3. ✅ 有 Token 时（cleaner 角色），能完成完整闭环：
   - 查看任务列表 → 进入详情 → 接单 → 开始 → 开门 → 完成（上传凭证）
4. ✅ `/cleaner/tasks` 可独立访问，与 `/customer`、`/` 路由共存
5. ✅ 移动布局在 375–480px 宽度下正常显示
