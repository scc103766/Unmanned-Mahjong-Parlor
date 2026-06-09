# 环境下载与补全清单

## 当前环境基线

指定 conda 环境：

- `anti-spoofing_scc_175`

已确认存在：

- Python 3.9.25
- FastAPI 0.125.0
- Pydantic 2.12.5
- Uvicorn 0.39.0

当前缺失或未在 PATH 中发现：

- SQLAlchemy
- Alembic
- asyncpg
- redis Python client
- pytest
- pytest-asyncio
- ruff
- mypy
- Node.js 与 npm/pnpm/yarn，用于当前 Web 前端主线

Flutter SDK 和 Dart 如已安装，可作为后续 App 迁移储备；近期主线不再要求 Android/iOS/桌面 App 打包。

## Web 前端依赖

当前主线建议先补 Web 前端工具链：

- Node.js 20 LTS 或更新 LTS
- npm、pnpm 或 yarn，推荐 pnpm

验证命令：

```bash
node --version
npm --version
corepack --version
```

启用 pnpm：

```bash
corepack enable
corepack prepare pnpm@latest --activate
pnpm --version
```

> 后续不需要重建环境，直接在 `anti-spoofing_scc_175` 里补包即可。

## Python 后端依赖

### 必装运行依赖

```bash
conda run -n anti-spoofing_scc_175 python -m pip install \
  "SQLAlchemy[asyncio]>=2.0.30" \
  "alembic>=1.13.2" \
  "asyncpg>=0.29.0" \
  "redis>=5.0.7" \
  "python-json-logger>=2.0.7"
```

说明：

- FastAPI、Pydantic、Uvicorn 当前环境已有，可暂不重复安装。
- `asyncpg` 用于 PostgreSQL 异步连接。
- `redis` 用于 Redis 健康检查、幂等、缓存和后续短期锁。
- `alembic` 用于数据库迁移。

### 必装开发依赖

```bash
conda run -n anti-spoofing_scc_175 python -m pip install \
  "pytest>=8.2.0" \
  "pytest-asyncio>=0.23.0" \
  "httpx>=0.27.0" \
  "ruff>=0.5.0" \
  "mypy>=1.10.0"
```

说明：

- `pytest`、`pytest-asyncio` 用于测试。
- `httpx` 用于 FastAPI TestClient 和 API 测试。
- `ruff` 用于 lint/format。
- `mypy` 用于类型检查。

## 数据库与缓存

### 方案 A：Docker 方式

下载并安装：

- Docker Engine 或 Docker Desktop
- Docker Compose 插件

项目中已有 `docker-compose.yml`，包含：

- PostgreSQL 16
- Redis 7
- API 服务

启动命令：

```bash
docker compose up --build
```

### 方案 B：本机服务方式

下载并安装：

- PostgreSQL 16 或兼容版本
- Redis 7 或兼容版本

需要准备数据库：

- 数据库名：`qipaishi`
- 用户名：`qipaishi`
- 密码：`qipaishi`

默认连接串在 `.env.example` 中：

```text
QIPAISHI_DATABASE_URL=postgresql+asyncpg://qipaishi:qipaishi@localhost:5432/qipaishi
QIPAISHI_REDIS_URL=redis://localhost:6379/0
```

## Flutter 客户端工具链（后续 App 迁移储备）

### 必装

下载并安装：

- Flutter SDK
- Git

说明：

- Flutter SDK 会自带 Dart，所以安装 Flutter 后通常不需要单独安装 Dart。
- 安装后需要把 `flutter/bin` 加入 `PATH`。

验证命令：

```bash
flutter --version
flutter doctor
```

## Android 端（后续 App 迁移储备）

下载并安装：

- Android Studio
- Android SDK
- Android SDK Command-line Tools
- Android SDK Platform Tools
- Android Emulator
- 至少一个 Android SDK Platform

验证命令：

```bash
flutter doctor --android-licenses
flutter devices
```

后续在客户端目录中运行：

```bash
cd clients/qipaishi_app
flutter pub get
flutter run -d android
flutter build apk
```

## iOS 端（后续 App 迁移储备）

仅 macOS 可构建 iOS。

下载并安装：

- Xcode
- Xcode Command Line Tools
- CocoaPods

验证命令：

```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
flutter doctor
```

后续在客户端目录中运行：

```bash
cd clients/qipaishi_app
flutter run -d ios
flutter build ipa
```

## Windows PC 端（后续 App 迁移储备）

仅 Windows 可构建 Windows 桌面应用。

下载并安装：

- Flutter SDK
- Git for Windows
- Visual Studio 2022
- Visual Studio 2022 的 “Desktop development with C++” 工作负载

后续在客户端目录中运行：

```powershell
cd clients/qipaishi_app
flutter run -d windows
flutter build windows
```

## macOS PC 端（后续 App 迁移储备）

仅 macOS 可构建 macOS 桌面应用。

下载并安装：

- Flutter SDK
- Xcode
- Xcode Command Line Tools

后续在客户端目录中运行：

```bash
cd clients/qipaishi_app
flutter run -d macos
flutter build macos
```

## Linux PC 端（后续 App 迁移储备）

如果需要 Linux 桌面包，下载并安装：

- Flutter SDK
- clang
- cmake
- ninja-build
- pkg-config
- GTK 3 开发库

Ubuntu/Debian 示例：

```bash
sudo apt-get update
sudo apt-get install -y clang cmake ninja-build pkg-config libgtk-3-dev
```

后续在客户端目录中运行：

```bash
cd clients/qipaishi_app
flutter run -d linux
flutter build linux
```

## 补全后的项目验证命令

### 后端

```bash
cd /supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi

conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
conda run -n anti-spoofing_scc_175 pytest
conda run -n anti-spoofing_scc_175 alembic upgrade head
conda run -n anti-spoofing_scc_175 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web 前端

创建 Web 工程后应验证：

```bash
cd /supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi/web

pnpm install
pnpm test
pnpm lint
pnpm build
```

### Flutter App（后续 App 迁移储备）

首次补全平台目录：

```bash
cd /supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi/clients/qipaishi_app

flutter create . --project-name qipaishi_app --org com.qipaishi --platforms android,ios,windows,macos
flutter pub get
flutter test
```

按目标平台运行：

```bash
flutter run -d android
flutter run -d ios
flutter run -d windows
flutter run -d macos
```

## 官方参考

- Flutter 支持平台：https://docs.flutter.dev/reference/supported-platforms
- Flutter 桌面支持：https://docs.flutter.dev/platform-integration/desktop
- Flutter 发布文档：https://docs.flutter.dev/deployment
- Flutter 手动安装：https://docs.flutter.dev/install/manual
