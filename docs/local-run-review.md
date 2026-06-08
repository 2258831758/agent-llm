# `docs/local-run.md` 评审与完善建议

## 1. 结论摘要

当前的 [`docs/local-run.md`](./local-run.md) 已经能覆盖“最短启动路径”，但还不够支撑第一次接手项目的人顺利完成本地运行和排障。主要问题不是内容太少，而是：

- 有几个关键前置条件没有写清楚。
- 有少量描述和实际代码行为不一致。
- 缺少“启动失败时先看哪里”的排障入口。

如果目标是让新同学 5 到 10 分钟内跑起来，这份文档至少还需要补一轮。

## 2. P0：建议优先补齐的内容

### 2.1 补上虚拟环境创建步骤

当前文档在 `docs/local-run.md:3-7` 直接使用 `venv\Scripts\python.exe` 安装依赖，但启动脚本本身也强依赖这个路径，见 `scripts/start-dev.ps1:12` 和 `scripts/start-dev.ps1:33-35`。

这意味着如果读者还没创建 `venv`，第一步就会失败。

建议补充：

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

同时建议在文档开头写明：

- 当前 quickstart 以 Windows PowerShell 为默认环境。
- 需要本机已安装可用的 Python 3.12+。

### 2.2 讲清默认数据库、Redis、LLM 的真实行为

当前文档在 `docs/local-run.md:15-30` 重点写了 MySQL / PostgreSQL / Redis 示例，但没有把“默认零配置能不能跑”说清楚。

实际情况是：

- 默认数据库已经是 SQLite，见 `.env.example:3`。
- 应用启动时 Redis 连不上不会阻塞启动，见 `backend/app/main.py:15-23`。
- 事件总线在 Redis 不可用时会退回进程内队列，见 `backend/app/services/events.py:36-42` 和 `backend/app/services/events.py:59-76`。
- `.env.example` 里 `LLM_ENABLED=true`，但 `DEEPSEEK_API_KEY` 默认是空的，见 `.env.example:8-11`。
- 没配 API Key 时不会启用真实模型审计，而是退回启发式结果，见 `backend/app/services/llm_review_service.py:701-705` 和 `backend/app/agent/nodes/llm_review.py:95-100`。

建议文档明确写成：

- “默认用 SQLite，可直接启动，不需要先准备 MySQL/PostgreSQL。”
- “Redis 是可选组件，不启动也能跑主流程，但健康检查里 `redis` 可能显示 `error`。”
- “如果没有 DeepSeek Key，建议显式设置 `LLM_ENABLED=false`，或者接受系统自动退回到启发式审计。”

建议补充的示例：

```env
LLM_ENABLED=false
```

以及：

```env
DEEPSEEK_API_KEY=your_api_key
LLM_ENABLED=true
```

### 2.3 修正 smoke test 的描述

当前文档在 `docs/local-run.md:73-78` 写的是“Upload the sample vulnerable project”，但脚本实际上传的是单个文件 `examples/vulnerable_python_app/app.py`，见 `scripts/smoke_test.py:14` 和 `scripts/smoke_test.py:20-23`。

另外这个脚本把后端地址写死在 `http://127.0.0.1:8000`，见 `scripts/smoke_test.py:9-10`。如果用户通过启动脚本改了端口，smoke test 会直接失效。

建议把文档改成更准确的说法：

- 当前 smoke test 上传的是示例项目中的单个 Python 文件，不是整个 demo 压缩包。
- 如果后端端口不是 `8000`，需要先修改脚本中的 `BASE_URL`。

### 2.4 增加“日志与常见失败”说明

当前文档虽然告诉用户用 `.\start.ps1` 和 `.\stop.ps1`，但没有告诉用户启动失败后先看什么。

而启动脚本其实已经约定了很明确的日志和报错路径，见 `scripts/start-dev.ps1:15-19` 与 `scripts/start-dev.ps1:82-88`。

建议新增一个“常见问题”小节，至少覆盖：

- `venv\Scripts\python.exe` 不存在。
- 端口 `3000` 或 `8000` 被占用，见 `scripts/start-dev.ps1:21-30` 和 `scripts/start-dev.ps1:45-47`。
- 已存在 `dev-processes.json`，需要先执行 `.\stop.ps1`，见 `scripts/start-dev.ps1:41-43`。
- 日志文件位置：
  - `backend/data/runtime/backend.out.log`
  - `backend/data/runtime/backend.err.log`
  - `backend/data/runtime/frontend.out.log`
  - `backend/data/runtime/frontend.err.log`

### 2.5 增加健康检查步骤

当前文档只有“打开前端”和“打开 Swagger”，但没有告诉用户如何快速验证后端是否真的活着。

项目实际提供了健康检查接口 `GET /api/v1/health`，见 `backend/app/api/routes/health.py:17-33`。

建议新增：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health
```

并说明预期结果：

- `database=ok` 说明数据库可用。
- `redis=error` 不一定代表主流程不可用，如果你本地没起 Redis，这个结果是符合当前实现的。

## 3. P1：建议补充但不是阻塞项

### 3.1 把启动脚本可选参数写出来

当前 `docs/local-run.md:33-49` 只写了 `.\start.ps1`，但脚本还支持：

- `-BackendPort`
- `-FrontendPort`
- `-OpenBrowser`

见 `scripts/start-dev.ps1:1-4`。

建议补充示例：

```powershell
.\start.ps1 -BackendPort 18000 -FrontendPort 13000 -OpenBrowser
```

同时注明：如果改了端口，`scripts/smoke_test.py` 默认不会自动跟着变。

### 3.2 把支持的上传方式写得更完整

当前 quickstart 没有说明“到底能传什么”。实际支持范围比文档体现得更完整：

- 单文件上传，见 `backend/app/api/routes/upload.py:55-91`
- 多文件上传，见 `backend/app/api/routes/upload.py:55-91`
- demo 项目上传，见 `backend/app/api/routes/upload.py:94-112`
- 压缩包解压，支持 `.zip`、`.tar`、`.tar.gz`、`.tgz`、`.tar.bz2`，见 `backend/app/services/files.py:13` 与 `backend/app/services/files.py:98-107`

建议在文档里单独写一个“支持的输入类型”小节。

### 3.3 增加报告导出方式说明

当前文档只写了报告目录 `backend/data/reports/{task_id}`，但没有告诉用户还能通过接口直接拿格式化结果。

建议补充：

- `GET /api/v1/report/{task_id}`
- `GET /api/v1/report/{task_id}?format=json`
- `GET /api/v1/report/{task_id}?format=markdown`
- `GET /api/v1/report/{task_id}?format=html`

这样更符合本地验证路径，也更方便联调。

### 3.4 加一个“最短验证闭环”

建议在文档里明确给出一个 3 步闭环：

1. `.\start.ps1`
2. 访问 `http://127.0.0.1:8000/api/v1/health`
3. 运行 `venv\Scripts\python.exe scripts\smoke_test.py`

这样新同学不需要自己猜“到底算不算启动成功”。

## 4. P2：体验优化项

### 4.1 统一文档语言

当前 `docs/local-run.md` 是英文 quickstart，但项目其他内容和界面更偏中文语境。建议后续统一成：

- 全中文
- 或中英双语

这样能减少使用过程中的语义切换成本。

### 4.2 加一个“当前限制”小节

虽然文档已经在 `docs/local-run.md:88-92` 提到 sandbox 是 stub，但还可以更完整一点，建议集中写在“当前限制”里：

- sandbox 仍是占位实现
- Redis 非强依赖
- 无 Key 时 LLM 走启发式回退
- 当前 smoke test 主要验证主链路，不代表生产级覆盖

### 4.3 增加 README 互链

建议在 `local-run.md` 顶部或结尾增加跳转：

- “想看完整项目说明，请回到 `README.md`”
- “想直接试接口，请打开 Swagger”

## 5. 推荐的新文档结构

建议把 `docs/local-run.md` 重组为下面这个顺序：

1. 适用环境
2. 一分钟快速启动
3. 环境变量最小配置
4. 可选配置
5. 启动与停止
6. 健康检查
7. Quick smoke test
8. 上传方式与报告导出
9. 日志与排障
10. 当前限制

这个结构比现在更适合“第一次跑项目”的读者，因为它先解决“能不能跑”，再展开“怎么调优”和“怎么排障”。

## 6. 可直接补入原文档的关键片段

### 6.1 最小可运行说明

```md
默认情况下，复制 `.env.example` 后即可使用 SQLite 本地运行，不需要先准备 MySQL 或 PostgreSQL。
Redis 也是可选的；如果本地没有启动 Redis，健康检查中的 `redis` 字段可能显示 `error`，但不影响基础审计流程。
```

### 6.2 无模型 Key 的说明

```md
如果你暂时没有 DeepSeek API Key，建议在 `.env` 中设置：

LLM_ENABLED=false

否则系统仍可运行，但会回退到启发式审计结果，而不是真实大模型审计。
```

### 6.3 健康检查说明

```md
启动完成后，先验证后端健康状态：

Invoke-WebRequest http://127.0.0.1:8000/api/v1/health

如果返回中 `database=ok`，说明数据库已初始化成功。
如果 `redis=error`，而你本地并未启动 Redis，这属于当前实现下的正常现象。
```

### 6.4 启动失败先看哪里

```md
如果 `.\start.ps1` 启动失败，优先检查：

- `backend/data/runtime/backend.err.log`
- `backend/data/runtime/frontend.err.log`
- 3000 / 8000 端口是否被占用
- 是否存在残留的 `scripts/dev-processes.json`
```

## 7. 额外发现：这不是文档问题，但会影响本地运行体验

在检查本地运行链路时，我还发现两个与“首次体验”直接相关、但不属于 `local-run.md` 本身的问题：

- `scripts/smoke_test.py` 的中文输出存在乱码。
- 前端脚本 `frontend/assets/app.js` 中也有明显乱码文本。

这两个问题不会直接阻止功能运行，但会显著影响第一次体验。建议把它们单独排进下一轮修复。

## 8. 建议的执行顺序

如果你准备真的动这份文档，我建议按下面顺序改：

1. 先补虚拟环境、SQLite/Redis/LLM 真实行为说明。
2. 再修 smoke test 描述和健康检查步骤。
3. 最后再补参数说明、上传方式、报告导出和排障。

这样一轮改完后，`docs/local-run.md` 就会从“能看懂”变成“真能带人跑起来”。
