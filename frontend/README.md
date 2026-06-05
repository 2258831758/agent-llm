# Frontend Placeholder

This repository currently ships a runnable backend MVP first.

The backend already exposes:

- `POST /api/v1/upload`
- `POST /api/v1/audit/start`
- `GET /api/v1/audit/{task_id}`
- `GET /api/v1/report/{task_id}`
- `WS /api/v1/ws/audit/{task_id}`

If you want, the next step can be a `Next.js 15 + Tailwind + Zustand + React Query` frontend that consumes these APIs.

