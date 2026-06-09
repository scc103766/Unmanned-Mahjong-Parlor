# 会话归档说明

每次对话结束后，PM Agent 按会话目的分类归档：

```
sessions/
├── project/     ← 项目推进相关：需求讨论、架构决策、任务管理、里程碑推进
└── meta/        ← 非项目相关：工具准备、知识问答、代理配置、环境调试
```

## 分类规则

| 类型 | 示例 | 归档到 |
|------|------|--------|
| 需求讨论、技术选型 | "为什么用XGBoost而不是随机森林" | `sessions/project/` |
| 任务审批、里程碑推进 | "批准M1-01，开始搭建src结构" | `sessions/project/` |
| 架构设计 | "五分支融合方案的细节" | `sessions/project/` |
| 代码审核 | "Engineer的代码这样写对吗" | `sessions/project/` |
| Skill 安装/配置 | "安装 superpowers skill" | `sessions/meta/` |
| 代理环境调试 | "vpn 命令怎么用" | `sessions/meta/` |
| 知识问答 | "AUC和F1的区别是什么" | `sessions/meta/` |
| 工具链搭建 | "CLI vs 插件模式的区别" | `sessions/meta/` |

## 文件命名

```
YYYY-MM-DD_简短描述.md
```

示例：
- `2026-06-04_双代理架构设计.md` → `sessions/project/`
- `2026-06-04_环境工具链准备.md` → `sessions/meta/`

## 归档时机

每次对话结束时，PM Agent 判断对话主题，自动写入对应的 sessions 目录。
