# Project Documentation Index

Generated: 2026-05-11

## Project Overview

- **Type:** 微信原生小程序端 brownfield 参考项目
- **Repository Shape:** 单体小程序项目
- **Primary Language:** JavaScript / WXML / WXSS
- **Architecture:** 小程序页面层 + REST API + 微信能力 + 硬件设备接口
- **Business Domain:** 24H 无人棋牌室/共享茶室管理系统

## Quick Reference

- **Entry Points:** `app.js`, `app.json`, `pages/index/index.js`
- **Network Layer:** `utils/http.js`
- **Hardware Layer:** `utils/lock.js`, `/member/**/open*` API
- **Core Customer Flow:** `index -> orderSubmit -> orderDetail`
- **Admin Flow:** `setStore*`, `setDoor*`, `SetOrder`, `statics`
- **Cleaning Flow:** `task`, `taskDetail`, `taskSettle`, `taskStatics`

## Generated Documentation

- [Project Context](./project-context.md)
- [Project Overview](./project-overview.md)
- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [API Contracts - Miniapp](./api-contracts-miniapp.md)
- [Component Inventory](./component-inventory.md)
- [Development Guide](./development-guide.md)

## Planning Artifacts

- [Product Brief](../_bmad-output/planning-artifacts/product-brief.md)
- [PRD](../_bmad-output/planning-artifacts/prd.md)

## Existing Documentation

- [README](../README.md) - 原始开源说明、功能介绍、服务端仓库链接和截图。
- [小程序部署文档.docx](../小程序部署文档.docx) - 原项目部署文档，当前未解析其内容。

## How To Use This Index

后续使用 BMAD 继续开发时，优先把本文件作为项目知识入口。创建架构、故事和实现任务时，至少引用：

1. `docs/project-context.md`
2. `docs/architecture.md`
3. `_bmad-output/planning-artifacts/prd.md`

