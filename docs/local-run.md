# AuditPilot Local Quickstart

## 1. Install dependencies

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Prepare environment

```powershell
Copy-Item .env.example .env
```

If you already started MySQL or PostgreSQL, change `DATABASE_URL` in `.env`.

Examples:

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/auditpilot
```

```env
DATABASE_URL=postgresql+psycopg://postgres:password@127.0.0.1:5432/auditpilot
```

Redis example:

```env
REDIS_URL=redis://127.0.0.1:6379/0
```

## 3. Start frontend + backend together

```powershell
.\start.ps1
```

This starts:

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

Stop both services with:

```powershell
.\stop.ps1
```

## 4. Open the web app

Frontend:

```text
http://127.0.0.1:3000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## 5. Quick smoke test

Keep the stack running, then use another terminal:

```powershell
venv\Scripts\python.exe scripts\smoke_test.py
```

The script will:

- Upload the sample vulnerable project
- Start the audit task
- Poll until completion
- Print report endpoints and finding summary

## 6. WebSocket logs

Connect to:

```text
ws://127.0.0.1:8000/api/v1/ws/audit/{task_id}
```

## Notes

- Sandbox is currently a stub implementation, but the API and workflow node are already reserved.
- Reports are generated to `backend/data/reports/{task_id}`.
- Uploads and extracted projects are stored under `backend/data/`.
