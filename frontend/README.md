# Health Tracking Frontend

React + Vite + TypeScript UI for the distributed health tracking system.

## Setup
1. From repository root:
   ```bash
   cd frontend
   cp .env.example .env
   npm install
   npm run dev
   ```
2. Open http://localhost:5173

## Environment
- VITE_API_BASE_URL (default http://localhost:8000)

## Features
- Register/login (JWT via gateway)
- Health records CRUD (steps, sleep_hours, weight)
- Analytics (average/total steps, record count)
- Auth context with token persistence, React Query data fetching
# Health Tracking Frontend

A React + Vite + TypeScript UI for the distributed Health Tracking system.

## Quickstart

```bash
cd frontend
cp .env.example .env   # adjust API base if not default
npm install
npm run dev            # open http://localhost:5173
```

- API base defaults to `http://localhost:8000` (gateway). Override with `VITE_API_BASE_URL`.
- Requires the backend stack running (`docker-compose up -d --build` from repo root).

## App Features
- Register & login (token stored locally).
- Create/read/update/delete health records for the logged-in user.
- View analytics (avg/total steps, record count) fed by events.
- Minimal dark UI with responsive layout.

## Project Structure
- `src/api` – thin API clients (auth, health, analytics).
- `src/state/auth.tsx` – auth context + storage.
- `src/routes` – pages via TanStack Router (home, login, register, dashboard).
- `src/styles.css` – theme tokens + layout primitives.

## Notes
- CORS is enabled on the API gateway; allowed origins are configured via `FRONTEND_ORIGINS` env (defaults include `http://localhost:5173`).
- Login uses form-encoded payload to match FastAPI OAuth2PasswordRequestForm.
- If analytics are empty, add records to trigger stats updates from the worker.
