# M0 验证报告

> 当前项目主线已调整为 Web-first。本文中的 Flutter 验证结果作为后续 App 迁移储备记录；近期后续开发以 Web 前端为主。

## 验证环境

- Python 环境：`anti-spoofing_scc_175`
- Flutter：3.41.9 stable（后续 App 迁移储备）
- Dart：3.11.5（后续 App 迁移储备）
- 可用 Flutter 设备：Linux desktop（后续 App 迁移储备）

## 后端验证

### Smoke

命令：

```bash
timeout 20 conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
```

结果：

```text
smoke ok
```

### Pytest

命令：

```bash
timeout 30 conda run -n anti-spoofing_scc_175 pytest -q
```

结果：

```text
3 passed in 0.02s
```

### Alembic

当前环境无法访问 Docker daemon，也无法从沙箱内连接 `127.0.0.1:5432` PostgreSQL。因此本轮使用 SQLite smoke 数据库验证迁移脚本。

命令：

```bash
QIPAISHI_DATABASE_URL=sqlite:///./dev.db timeout 30 conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db timeout 20 conda run -n anti-spoofing_scc_175 alembic current
```

结果：

```text
20260513_0001 (head)
```

已创建表：

- `tenants`
- `tenant_apps`
- `users`
- `roles`
- `user_roles`
- `user_store_scopes`
- `audit_logs`
- `alembic_version`

真实 PostgreSQL 迁移待当前 shell 具备可访问的 PostgreSQL 服务后执行：

```bash
conda run -n anti-spoofing_scc_175 alembic upgrade head
```

## Flutter 验证（后续 App 迁移储备）

### Flutter Doctor

命令：

```bash
flutter doctor -v
```

关键结果：

- Flutter SDK 可用：3.41.9 stable
- Dart 可用：3.11.5
- Linux desktop 目标可用
- Android SDK 未配置
- Chrome 未配置

### 生成 Linux 平台目录

命令：

```bash
flutter create . --project-name qipaishi_app --org com.qipaishi --platforms linux
```

结果：

```text
Got dependencies.
Wrote 14 files.
```

### Pub Get

命令：

```bash
flutter pub get
```

结果：

```text
Got dependencies!
```

### Flutter Test

命令：

```bash
flutter test
```

结果：

```text
All tests passed!
```

### Linux Build

命令：

```bash
flutter build linux
```

结果：

```text
Built build/linux/x64/release/bundle/qipaishi_app
```

### Linux Run

命令：

```bash
timeout 25 flutter run -d linux
```

结果：

```text
Built build/linux/x64/debug/bundle/qipaishi_app
error while loading shared libraries: libgtk-3.so.0: cannot open shared object file: No such file or directory
Error launching application on Linux.
```

`ldd` 确认缺失：

```text
libgtk-3.so.0 => not found
libgdk-3.so.0 => not found
```

需要补充 Linux 桌面运行时：

```bash
sudo apt-get update
sudo apt-get install -y libgtk-3-0
```

安装后重试：

```bash
cd /supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi/clients/qipaishi_app
flutter run -d linux
```
