# M5 设备控制验证报告

## 交付范围

本轮进入 M5，完成设备控制首版后端闭环：设备配置、设备命令、mock 设备适配器、订单授权开门开锁开电，以及命令查询。

已实现：

- 设备表：
  - `devices`
  - 支持门店大门、房间门、智能锁、电源等 `device_type`
  - 支持 `provider`、`external_id`、`capabilities` 和启停状态
- 设备命令表：
  - `device_commands`
  - 记录设备、操作者、业务对象、命令、状态、请求、响应、失败原因和执行时间
  - 支持 `idempotency_key`，同租户内唯一
- mock adapter：
  - `mock` provider 可执行成功命令
  - `external_id=mock_fail` 可模拟失败响应
- 设备管理接口：
  - `GET /api/v1/devices`
  - `POST /api/v1/devices`
  - `GET /api/v1/device-commands`
- 订单授权设备接口：
  - `POST /api/v1/orders/{order_id}/open-store-door`
  - `POST /api/v1/orders/{order_id}/open-room-door`
  - `POST /api/v1/orders/{order_id}/open-room-lock`
  - `POST /api/v1/orders/{order_id}/power-on`
- 订单设备授权规则：
  - 仅 `paid`、`in_use` 订单可操作设备
  - 默认允许订单开始前 15 分钟到结束后 30 分钟内操作
  - 顾客只能操作自己的订单；商家、店员、客服可按租户管理权限操作
  - 每次操作写 `device_commands` 和审计日志
- Alembic 迁移：`20260515_0008_device_control.py`

## 当前边界

- 真实硬件供应商尚未接入；当前 provider 为 mock adapter。
- 设备命令已经支持幂等键，但还未实现失败重试接口和短时间限流策略。
- 商家主动测试设备和后台开关门目前可通过订单授权路径覆盖订单场景，独立设备测试接口后续补齐。
- 保洁任务授权开门会在 M6 保洁闭环中接入同一套 `DeviceCommand` 服务。

## 验证命令

```bash
conda run -n anti-spoofing_scc_175 pytest -q
conda run -n anti-spoofing_scc_175 ruff check app tests
conda run -n anti-spoofing_scc_175 mypy app
conda run -n anti-spoofing_scc_175 python scripts/smoke_api.py
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic upgrade head
QIPAISHI_DATABASE_URL=sqlite:///./dev.db conda run -n anti-spoofing_scc_175 alembic current
QIPAISHI_DATABASE_URL=sqlite:////tmp/qipaishi_m5_device_control.db conda run -n anti-spoofing_scc_175 alembic upgrade head
```

结果：

```text
pytest: 38 passed
ruff: All checks passed
mypy: Success: no issues found in 96 source files
smoke: smoke ok
alembic: 20260515_0008 (head)
OpenAPI paths: 62
```

## 下一步

继续 M5/M6 衔接：

1. 增加商家独立设备测试、失败重试和短时间限流接口。
2. 将设备命令异常接入平台异常列表和 Hermes 只读摘要。
3. 进入 M6：订单完成后生成保洁任务，保洁任务授权开门复用 `DeviceCommand`。
