# AuditPilot

AuditPilot 是一个基于 FastAPI + LangGraph 的代码安全审计原型，支持把源码文件、多个文件、目录或压缩包作为一个项目上下文上传，然后结合静态规则和 LLM 联动分析输出审计报告。

当前仓库已经具备这些能力：

- 多文件 / 目录 / 压缩包上传
- 项目级静态扫描
- 跨文件上下文 LLM 复核
- WebSocket 实时进度与日志
- HTML / Markdown / JSON 报告导出
- 基础漏洞基线覆盖：SQL 注入、命令注入、SSRF、XSS、PHP 反序列化、路径穿越、XXE、SSTI、开放重定向、硬编码密钥、依赖漏洞等

## 架构概览

运行流程：

1. 上传源码、目录或压缩包
2. 解压 / 组装项目上下文
3. 识别语言、框架、入口文件
4. 执行静态扫描
5. 组装跨文件记忆体并调用 LLM 复核
6. 合并结果、映射 OWASP / CWE、生成报告

主要目录：

```text
backend/
  app/
    agent/        LangGraph 工作流与节点
    api/          FastAPI 路由
    scanners/     启发式扫描器
    services/     审计、报告、LLM、文件处理
  data/           SQLite、上传、解压项目、报告、漏洞知识库

frontend/
  index.html
  assets/

scripts/
  start-dev.ps1
  stop-dev.ps1
  smoke_test.py
```

## 环境要求

- Python 3.12+
- Windows PowerShell（仓库自带启动脚本基于 PowerShell）
- 可选：Redis
- 可选：DeepSeek API Key（启用真实 LLM 审计时需要）

默认配置：

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:3000`
- Swagger：`http://127.0.0.1:8000/docs`
- 数据库：默认 SQLite，文件在 `backend/data/auditpilot.db`

## 使用方式

### 1. 安装依赖

先准备虚拟环境，然后安装依赖：

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果你还没创建虚拟环境：

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 准备环境变量

复制示例配置：

```powershell
Copy-Item .env.example .env
```

如果要启用真实 LLM 审计，在 `.env` 里配置：

```env
DEEPSEEK_API_KEY=your_api_key
LLM_ENABLED=true
```

如果暂时只想跑本地规则扫描，也可以把 LLM 关掉：

```env
LLM_ENABLED=false
```

可选配置：

```env
DATABASE_URL=sqlite:///./backend/data/auditpilot.db
REDIS_URL=redis://127.0.0.1:6379/0
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

说明：

- `Redis` 当前不是强依赖，连不上不会阻止服务启动
- 默认数据库是 SQLite，最省事，适合本地开发

### 3. 启动前后端

仓库已经提供一键脚本：

```powershell
.\start.ps1
```

停止服务：

```powershell
.\stop.ps1
```

启动成功后可以访问：

- 前端：`http://127.0.0.1:3000`
- 后端：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`

运行日志会写入：

```text
backend/data/runtime/backend.out.log
backend/data/runtime/backend.err.log
backend/data/runtime/frontend.out.log
backend/data/runtime/frontend.err.log
```

### 4. 在页面里发起审计

打开前端后，典型使用流程是：

1. 填写任务名称
2. 上传源码
   - 任意单个文件
   - 多个文件
   - ZIP / TAR.GZ 压缩包
   - 目录
3. 点击“启动审计”
4. 等待前端实时显示进度和日志
5. 审计完成后查看漏洞详情和报告预览

现在上传逻辑是“项目级”的，不是单文件孤立扫描。也就是说：

- 多个文件会一起进入同一个审计任务
- LLM 会按入口、调用关系、导入关系和扫描命中结果拼接上下文
- 结果里会展示 `related_files`，帮助你看到一个问题牵涉了哪些文件

### 5. 运行快速冒烟测试

在保持服务运行的情况下，开新终端执行：

```powershell
venv\Scripts\python.exe scripts\smoke_test.py
```

这个脚本会：

- 上传示例项目
- 启动审计
- 轮询直到完成
- 输出报告路径和漏洞摘要

## 手动启动方式

如果你不想用 `start.ps1`，也可以手动分别启动前后端。

### 启动后端

```powershell
venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 启动前端

前端当前是静态页面，可以直接用任意静态文件服务：

```powershell
cd frontend
..\venv\Scripts\python.exe -m http.server 3000 --bind 127.0.0.1
```

## 部署方式

### 方式一：单机手动部署

适合内网环境、测试机或 PoC 环境。

部署思路：

1. 把仓库代码放到目标机器
2. 创建虚拟环境并安装依赖
3. 准备 `.env`
4. 启动 FastAPI
5. 用 Nginx 或任意静态服务器托管 `frontend/`
6. 反向代理前端和后端

Linux 上的后端启动命令示例：

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

前端可以直接被 Nginx 托管，因为它本质上是静态文件：

```text
frontend/index.html
frontend/assets/
```

### 方式二：Windows 服务化部署

如果目标机器是 Windows，可以沿用当前 PowerShell 启动方式，再把后端和静态前端接到 IIS 或 Nginx 前面。

建议：

- 后端长期运行用 `uvicorn` 配合 NSSM / WinSW 做成服务
- 前端直接由 IIS、Nginx 或静态文件服务器提供
- 日志目录保留在 `backend/data/runtime/`

### 方式三：Nginx 反向代理部署

一个常见部署方式是：

- `Nginx` 对外提供 `80/443`
- `frontend/` 作为静态站点
- `/api/` 和 `/docs` 代理到 FastAPI

示例配置：

```nginx
server {
    listen 80;
    server_name your-host;

    root /opt/auditpilot/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }
}
```

如果你需要 WebSocket 日志流，记得为对应路径开启升级头：

```nginx
location /api/v1/ws/ {
    proxy_pass http://127.0.0.1:8000/api/v1/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## 常用接口

上传：

```http
POST /api/v1/upload
```

支持：

- `file`
- `files[]`
- 目录文件集合

启动任务：

```http
POST /api/v1/audit/start
```

查询任务：

```http
GET /api/v1/audit/{task_id}
```

获取报告：

```http
GET /api/v1/report/{task_id}
GET /api/v1/report/{task_id}?format=json
GET /api/v1/report/{task_id}?format=markdown
GET /api/v1/report/{task_id}?format=html
```

WebSocket 实时日志：

```text
ws://127.0.0.1:8000/api/v1/ws/audit/{task_id}
```

## 数据落盘位置

运行过程中会在 `backend/data/` 下生成这些内容：

```text
backend/data/
  auditpilot.db              SQLite 数据库
  uploads/                   原始上传内容
  projects/                  解压或组装后的项目目录
  reports/                   审计报告
  runtime/                   启动日志
  vulnerability_library/     漏洞知识库
```

## 当前实现说明

和一些更完整的企业版审计平台相比，这个仓库当前更接近“可运行原型”，特点是：

- 前端是静态页面，不依赖打包工具
- 后端工作流已经完整串起来
- Docker sandbox 目前仍是预留节点，不是完整隔离执行环境
- 漏洞发现主要来自：
  - 基础启发式规则
  - 简化版扫描器
  - LLM 跨文件复核

所以它很适合：

- 本地演示
- 教学
- 漏洞规则原型验证
- 做你自己的审计平台二次开发底座

## 后续建议

如果你准备继续往可用产品推进，比较值的方向是：

1. 把扫描规则按语言拆细，例如 PHP / Java / Node.js 专项规则
2. 引入真正的 taint analysis 或 AST 分析，而不只是文本启发式
3. 把 sandbox 从占位实现升级为真实隔离执行环境
4. 给前端补任务列表、历史报告和规则管理
5. 增加 Docker Compose / CI / 生产部署脚本

