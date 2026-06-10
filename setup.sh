#!/usr/bin/env bash
set -euo pipefail

# ================================================================
# 24H 无人棋牌室 — 一键环境搭建脚本
# ================================================================
# 用法:
#   chmod +x setup.sh && ./setup.sh
#
# 可选参数:
#   ./setup.sh --db postgres  使用 PostgreSQL（需Docker）
#   ./setup.sh --db sqlite    使用 SQLite（无需外部依赖，默认）
# ================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/python_24_qipaishi"
WEB_DIR="$PROJECT_DIR/web"
DB_MODE="${1:-sqlite}"
DB_FLAG="${2:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "========================================"
echo " 24H 无人棋牌室 — 环境搭建"
echo "========================================"
echo ""

# ---- 1. Python 环境 ----
log "检查 Python..."
python3 --version || err "请安装 Python 3.11+"

if command -v conda &>/dev/null && conda env list 2>/dev/null | grep -q "qipaishi"; then
    log "使用已有 conda 环境: qipaishi"
    PYTHON_CMD="conda run -n qipaishi python"
    PIP_CMD="conda run -n qipaishi pip"
elif [ -d "$PROJECT_DIR/.venv" ]; then
    log "使用已有 venv"
    PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"
    PIP_CMD="$PROJECT_DIR/.venv/bin/pip"
else
    log "创建 virtualenv..."
    python3 -m venv "$PROJECT_DIR/.venv"
    PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"
    PIP_CMD="$PROJECT_DIR/.venv/bin/pip"
fi

# ---- 2. Python 依赖 ----
log "安装 Python 依赖..."
cd "$PROJECT_DIR"
$PIP_CMD install -e ".[dev]" -q

# ---- 3. 环境变量 ----
if [ ! -f "$PROJECT_DIR/.env" ]; then
    log "创建 .env 配置..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
fi

# 根据数据库模式调整 DATABASE_URL
if [ "$DB_MODE" = "sqlite" ] || [ "$DB_FLAG" = "--sqlite" ]; then
    log "使用 SQLite (无需外部数据库)"
    export QIPAISHI_DATABASE_URL="${QIPAISHI_DATABASE_URL:-sqlite+aiosqlite:///./dev.db}"
    export QIPAISHI_HEALTH_CHECK_DATABASE="${QIPAISHI_HEALTH_CHECK_DATABASE:-false}"
    export QIPAISHI_HEALTH_CHECK_REDIS="${QIPAISHI_HEALTH_CHECK_REDIS:-false}"
else
    log "使用 PostgreSQL (需 Docker)"
    export QIPAISHI_DATABASE_URL="${QIPAISHI_DATABASE_URL:-postgresql+asyncpg://qipaishi:qipaishi@localhost:5432/qipaishi}"
    # 启动 PostgreSQL
    if ! docker ps 2>/dev/null | grep -q "qipaishi-postgres"; then
        docker compose up -d postgres redis 2>/dev/null || warn "Docker未运行，跳过PostgreSQL启动"
    fi
fi

export QIPAISHI_CORS_ORIGINS="${QIPAISHI_CORS_ORIGINS:-http://localhost:5173,http://127.0.0.1:5173}"

# ---- 4. 数据库迁移 ----
log "执行数据库迁移..."
QIPAISHI_DATABASE_URL="$QIPAISHI_DATABASE_URL" $PYTHON_CMD -m alembic upgrade head

# ---- 5. Node.js 依赖 ----
if command -v node &>/dev/null; then
    log "安装前端依赖..."
    cd "$WEB_DIR"
    npm install --silent 2>/dev/null || warn "npm install 失败，请手动执行: cd web && npm install"
else
    warn "未检测到 Node.js，跳过前端依赖安装"
fi

cd "$PROJECT_DIR"

# ---- 6. 验证 ----
log "运行后端测试..."
QIPAISHI_DATABASE_URL="$QIPAISHI_DATABASE_URL" $PYTHON_CMD -m pytest -q 2>/dev/null && log "测试通过" || warn "部分测试未通过（可能缺少 Redis）"

log "验证 API 健康检查..."
QIPAISHI_DATABASE_URL="$QIPAISHI_DATABASE_URL" QIPAISHI_CORS_ORIGINS="$QIPAISHI_CORS_ORIGINS" \
    $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 3

if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
    log "API 服务正常: http://127.0.0.1:8000/health"
else
    warn "API 未响应，请检查日志"
fi

# 创建开发 token
TOKEN_RESP=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/dev-bootstrap \
    -H 'content-type: application/json' \
    -d '{"tenant_name":"示例棋牌室","client_type":"h5","app_id":"dev-h5"}')
TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")

echo ""
echo "========================================"
echo " 环境搭建完成！"
echo "========================================"
echo ""
echo " 📡 API 服务:  http://127.0.0.1:8000"
echo " 📖 API 文档:  http://127.0.0.1:8000/docs"
echo " 🌐 前端开发:  cd web && npm run dev"
echo ""

if [ -n "$TOKEN" ]; then
    echo " 🔑 开发 Token (管理员):"
    echo "    $TOKEN"
    echo ""
fi

echo " 🏢 商家后台:  http://localhost:5173/"
echo " 📱 顾客 H5:   http://localhost:5173/customer"
echo " 🧹 保洁 H5:   http://localhost:5173/cleaner"
echo " 🔧 平台后台:  http://localhost:5173/platform"
echo ""
echo " 启动后端:     cd python_24_qipaishi && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo " 启动前端:     cd python_24_qipaishi/web && npm run dev"
echo ""

# 保持 API 运行，Ctrl+C 停止
wait $API_PID 2>/dev/null
