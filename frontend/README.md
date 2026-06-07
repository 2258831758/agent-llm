# Frontend

这个目录现在是独立的前端入口，和后端 API 分开部署、分开启动。

当前实现是一个轻量静态前端：

- `frontend/index.html`
- `frontend/assets/styles.css`
- `frontend/assets/app.js`

默认开发访问方式：

- 前端: `http://127.0.0.1:3000`
- 后端: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

启动方式仍然使用仓库根目录下的：

- `.\start.ps1`
- `.\stop.ps1`

前端会直接调用后端这些接口：

- `POST /api/v1/upload`
- `POST /api/v1/upload/demo`
- `POST /api/v1/audit/start`
- `GET /api/v1/audit/{task_id}`
- `GET /api/v1/report/{task_id}`
- `WS /api/v1/ws/audit/{task_id}`
