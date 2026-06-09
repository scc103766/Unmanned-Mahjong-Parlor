# M8 环境依赖落地体检

## 结论

当前 `anti-spoofing_scc_175` 环境已经可以支撑无人棋牌室项目继续落地开发：

- Python 后端核心依赖可用。
- `aiosqlite 0.22.1` 已安装，可用于本地 SQLite 异步运行时。
- Vue/Vite 前端依赖可用，生产构建通过。
- 后端全量测试、smoke、Alembic 当前版本检查通过。
- 本地 HTTP 链路已验证：`dev-bootstrap` 登录和商家工作台查询均返回 200。

## 已确认依赖

Python 环境：

```text
python: /home/scc/anaconda3/envs/anti-spoofing_scc_175/bin/python
fastapi==0.125.0
SQLAlchemy==2.0.49
alembic==1.16.5
uvicorn==0.39.0
pydantic==2.12.5
asyncpg==0.31.0
redis==7.0.1
httpx==0.28.1
pytest==8.4.2
pytest-asyncio==1.2.0
ruff==0.15.12
mypy==1.19.1
aiosqlite==0.22.1
```

前端环境：

```text
node: v22.22.0
npm: 11.13.0
vue: 3.5.34
vite: 6.4.2
typescript: 5.9.3
vue-tsc: 2.2.12
pinia: 2.3.1
vue-router: 4.6.4
axios: 1.16.1
```

## 本轮修复

- 删除了项目根目录临时 `aiosqlite.py` shim，避免遮蔽环境中的正式 `aiosqlite` 包。
- 将 `aiosqlite>=0.20.0` 加入 `pyproject.toml` 的 dev 依赖。
- 修复 FastAPI DB 依赖入口：`get_db_session()` 现在先创建 `async_sessionmaker`，再打开实际 session。
- 补充测试覆盖 DB session factory 打开路径。
- README 补充 SQLite 运行 FastAPI 的正确 URL：`sqlite+aiosqlite:///./dev.db`。

## 验证结果

```text
ruff: All checks passed
mypy: Success, 122 source files
pytest: 68 passed
smoke: smoke ok
alembic current: 20260515_0012 (head)
npm build: passed
aiosqlite select 1: passed
SQLAlchemy sqlite+aiosqlite select 1: passed
HTTP /health: 200
HTTP /api/v1/auth/dev-bootstrap: 200
HTTP /api/v1/analytics/dashboard: 200
CORS http://localhost:5173: allowed
LAN Web http://192.168.17.175:5173: 200
LAN API http://192.168.17.175:8000/health: 200
LAN API dev-bootstrap/dashboard via http://192.168.17.175:8000: 200
```

## 剩余环境提醒

- `python-json-logger` 在 `pyproject.toml` 主依赖中声明，但当前环境未安装；现有代码实际未 import 它，所以不阻塞运行。若要做严格依赖一致性，应补装或移除该声明。
- `pip check` 报出环境级冲突：`opencv-python-headless 4.13.0.92` 要求 `numpy>=2`，当前为 `numpy 1.26.4`。本项目不使用 OpenCV，不影响无人棋牌室后端和 Web 前端。
- 生产落地仍需要实际 PostgreSQL、Redis、支付/设备供应商配置和部署参数，不应只依赖 SQLite 开发库。
