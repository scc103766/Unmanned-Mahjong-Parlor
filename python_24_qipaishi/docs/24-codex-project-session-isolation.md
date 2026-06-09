# Codex 项目级会话隔离方案

## 目标

Codex 会话按项目隔离：

- 同一个项目共享同一组 Codex 会话、历史和状态。
- 不同项目默认不共享会话、历史和状态。
- 需要读取其他项目会话信息时，必须明确指定项目路径或会话 ID。

## 实现方式

使用项目专属 `CODEX_HOME`：

```text
~/.codex-projects/<project-name>-<project-path-hash>/
```

本项目入口脚本：

```bash
./scripts/codex_project_session.sh
```

脚本会：

- 根据当前项目绝对路径生成稳定 project slug。
- 设置 `CODEX_HOME` 到项目专属目录。
- 复用全局 `~/.codex/auth.json` 认证文件。
- 复用全局 `~/.codex/skills` 技能目录。
- 创建只信任当前项目路径的 `config.toml`。
- 将会话、history、日志、状态库保存在项目专属 `CODEX_HOME`。

## 常用命令

初始化当前项目 Codex home，但不启动 Codex：

```bash
./scripts/codex_project_session.sh --init-only
```

查看当前项目会使用的隔离目录：

```bash
./scripts/codex_project_session.sh --print-env
```

启动当前项目 Codex：

```bash
./scripts/codex_project_session.sh
```

恢复当前项目中的某个会话：

```bash
./scripts/codex_project_session.sh resume <session-id>
```

## 访问其他项目会话

默认不能访问其他项目会话。确实需要时，必须显式指定另一个项目的 `CODEX_HOME`：

```bash
CODEX_PROJECT_HOME=/home/scc/.codex-projects/<other-project-slug> \
  ./scripts/codex_project_session.sh resume <other-session-id>
```

推荐在执行前先记录来源项目路径，并在回复中说明跨项目信息来自哪里。

## 迁移旧会话

旧的全局 `~/.codex` 会话不会自动迁入项目目录。需要迁移时应人工挑选：

1. 明确旧会话属于哪个项目。
2. 只迁移该项目相关 session。
3. 不把多个项目的历史混放到同一个项目 `CODEX_HOME`。

## 本项目约定

本项目边界：

```text
/supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi
```

后续无人棋牌室项目的 Codex 开发、恢复和上下文延续都应通过本脚本进入。
