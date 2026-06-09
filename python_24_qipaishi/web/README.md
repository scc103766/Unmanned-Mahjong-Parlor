# Qipaishi Web

M8 Web 正式工程化首版。当前使用 Vue 3 + Vite + TypeScript，已具备商家后台路由、Pinia 登录态、权限守卫、类型化 API client 和运营核心页面。

```bash
cd web
npm install
npm run dev
```

默认访问：

```text
http://127.0.0.1:5173
```

局域网分享测试可访问：

```text
Web: http://192.168.17.175:5173
API: http://192.168.17.175:8000
```

页面默认会将 API 地址推导为 `http://<当前页面 hostname>:8000`。如果测试者从其他域名或转发地址访问，在页面右上角手动填写对应 API 地址即可。

构建校验：

```bash
npm run build
```

页面在未写入 Bearer Token 时会展示本地样例数据；连接 FastAPI 后端后可通过“开发登录”调用 `/api/v1/auth/dev-bootstrap` 写入开发管理员 token。
