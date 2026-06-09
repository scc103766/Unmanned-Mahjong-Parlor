# Agent Session Isolation

This project uses project-scoped Codex sessions.

- Start Codex for this project through `scripts/codex_project_session.sh`.
- Same project sessions share the same project `CODEX_HOME`.
- Sessions from other projects must not be resumed or read by default.
- If cross-project context is needed, the user must explicitly name the other project path or session id.
- Do not copy session history, logs, or memory files between project homes unless the user explicitly asks for that transfer.
- Shared authentication or skills may be symlinked from the global Codex home; conversation/session state must stay project-local.

For this repository, the project boundary is:

```text
/supercloud/llm-code/scc/scc/project_robot/python_24_qipaishi
```
