# 24H 无人棋牌室管理系统

> 面向自助棋牌室、共享茶室、台球室等无人空间的 SaaS 运营平台。

[![M8 Complete](https://img.shields.io/badge/Milestone-M8%20完成-brightgreen)](#里程碑)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.125-009688)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-4fc08d)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178c6)](https://typescriptlang.org)

---

## 产品定位

帮助商家把 **"预约 → 支付 → 到店 → 开门 → 用电 → 保洁 → 结算 → 统计"** 串成一个稳定闭环，让门店在低人工值守甚至无人值守状态下持续营业。

### 四端覆盖

| 端 | 路径 | 用户 | 布局 |
|----|------|------|------|
| 🏢 **商家后台** | `/` | 商家/店长/店员 | 桌面侧边栏 |
| 📱 **顾客 H5** | `/customer` | 消费者 | 移动端底部Tab |
| 🧹 **保洁 H5** | `/cleaner` | 保洁员 | 移动端底部Tab |
| 🔧 **平台后台** | `/platform` | 平台运营方 | 桌面侧边栏 |

---

## 技术栈

| 层次 | 方案 |
|------|------|
| 后端框架 | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.x + Alembic |
| 数据库 | PostgreSQL (生产) / SQLite+aiosqlite (开发) |
| 缓存/幂等 | Redis |
| Web 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router |
| 测试 | pytest + httpx + ruff + mypy |
| 部署 | Docker Compose |
| 参考项目 | 微信原生小程序 (`24h_qipaishi/`) |
| App (预留) | Flutter 3.x 骨架 (`clients/qipaishi_app/`) |

---

## 快速开始

### 从零复现（推荐）

```bash
git clone https://github.com/scc103766/Unmanned-Mahjong-Parlor.git
cd Unmanned-Mahjong-Parlor
chmod +x setup.sh && ./setup.sh
```

一条命令完成：Python 虚拟环境 → 依赖安装 → 数据库迁移 → API 启动 → 开发 Token 生成。

### 手动搭建

#### 环境要求

- Python 3.11+
- Node.js 22+
- conda (推荐)

### 1. 启动后端

```bash
cd python_24_qipaishi

# 安装依赖
pip install -e ".[dev]"

# 数据库迁移（开发用SQLite）
QIPAISHI_DATABASE_URL=sqlite+aiosqlite:///./dev.db alembic upgrade head

# 启动API服务
QIPAISHI_DATABASE_URL=sqlite+aiosqlite:///./dev.db \
QIPAISHI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173 \
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://127.0.0.1:8000/docs` 查看 OpenAPI 文档（96 个路径）。

### 2. 创建首个租户和 Token

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/dev-bootstrap \
  -H 'content-type: application/json' \
  -d '{"tenant_name":"示例棋牌室","client_type":"h5","app_id":"dev-h5"}'
```

返回的 `access_token` 用于前端登录。

### 3. 启动前端

```bash
cd web
npm install
npm run dev
```

打开浏览器访问：
- 商家后台：`http://localhost:5173/`
- 顾客 H5：`http://localhost:5173/customer`
- 保洁 H5：`http://localhost:5173/cleaner`
- 平台后台：`http://localhost:5173/platform`

### 4. Docker Compose 部署（生产）

```bash
docker compose up --build
```

---

## 项目结构

```
python_24_qipaishi/
├── app/
│   ├── api/v1/routers/     # API 路由 (22个模块)
│   ├── core/               # 配置/错误/日志/安全
│   ├── db/                 # 数据库迁移 (12个版本)
│   └── modules/            # 业务模块 (17个领域)
│       ├── auth/           # 认证
│       ├── tenancy/        # 多租户
│       ├── stores/         # 门店
│       ├── rooms/          # 房间/价格
│       ├── orders/         # 订单/库存锁
│       ├── payments/       # 支付/退款
│       ├── wallet/         # 余额/充值
│       ├── coupons/        # 优惠券
│       ├── group_buy/      # 团购码
│       ├── devices/        # 设备控制
│       ├── cleaning/       # 保洁任务
│       ├── analytics/      # 经营统计
│       ├── withdrawals/    # 提现
│       ├── members/        # 会员
│       ├── operations/     # 异常/审计/补偿
│       └── pricing/        # 价格试算
├── web/                    # Vue 3 前端工程
│   └── src/
│       ├── layouts/        # 四端布局
│       │   ├── merchant/   # 商家后台
│       │   ├── customer/   # 顾客H5
│       │   ├── cleaner/    # 保洁H5
│       │   └── platform/   # 平台后台
│       ├── modules/        # 业务视图 (27个页面)
│       └── core/api/       # API客户端 (5个模块)
├── tests/                  # pytest (68 cases)
├── clients/qipaishi_app/   # Flutter App 骨架
├── docs/                   # 25份规划与验证文档
└── docker-compose.yml      # 容器化部署
```

---

## 里程碑

| 阶段 | 内容 | 状态 |
|------|------|------|
| M0 | 项目基础：FastAPI骨架/迁移/测试/OpenAPI 96路径 | ✅ |
| M1 | 租户权限：多租户/RBAC/JWT/审计 | ✅ |
| M2 | 门店房间：门店/房间/价格/禁用时段 | ✅ |
| M3 | 预约订单：库存锁/状态机/续费/换房 | ✅ |
| M4 | 支付资金：Mock支付/余额/优惠券/团购 | ✅ |
| M5 | 设备控制：命令表/Mock适配器/权限校验 | ✅ |
| M6 | 保洁闭环：任务流/房态联动/结算 | ✅ |
| M7 | 商家运营：统计/提现/改时/补偿 | ✅ |
| M8 | Web前端：商家+顾客+保洁+平台 四端完成 | ✅ |
| M9 | 联调试运营：真实支付/硬件对接/部署上线 | ⏳ |

---

## 核心特性

- **强业务边界**：订单库存锁、支付回调、设备控制、退款提现全部在服务端裁决，前端不作为可信来源
- **多租户隔离**：以登录态/应用绑定/门店授权/数据作用域为准，不信任前端 `tenant-id`
- **支付幂等**：微信回调、退款、余额流水均具备幂等键和事件表
- **设备审计**：每次开门/开电/开锁绑定操作者、角色、订单/任务、时间、结果，全程可追溯
- **房态联动**：订单结束自动触发保洁，脏房预约策略可配置
- **移动优先**：顾客端和保洁端采用 480px 移动视口，桌面端自适应布局

---

## 质量指标

```
后端测试: 68 passed (M1–M8 全覆盖)
代码检查: ruff ✅ / mypy ✅ (122 源文件)
Alembic:  12 迁移版本
OpenAPI:  96 路径
前端构建: 156 模块, 0 TypeScript 错误, 47 chunks
```

---

## 参考项目

`24h_qipaishi/` — 微信原生小程序，包含约 50 个页面，覆盖完整的顾客预约/支付/开门、商家管理、保洁任务闭环。作为业务参考和字段对齐来源，规划中通过兼容层 `/compat/member/**` 映射到新 API。

---

## 开发方法论

本项目使用 [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) 进行 brownfield 分析驱动的开发：

```
BMAD 分析 (24h_qipaishi 小程序源码)
  → PRD / Product Brief
  → 架构设计 / 领域模型 / API规划
  → 里程碑拆解 (M0–M9)
  → Sprint 执行 + 验证报告
```

详细规划文档见 `python_24_qipaishi/docs/`。
