# controltwin-frontend

Production-ready React frontend for **ControlTwin** (ICS/SCADA Digital Twin), integrated with FastAPI backend.

## Stack

- React 18 + JavaScript (Vite 5)
- Tailwind CSS v3 (dark OT theme)
- React Router v6
- Axios (JWT interceptors)
- Zustand (auth + alerts)
- TanStack React Query v5
- Recharts (time series + alerts trend)
- React Flow + Dagre (ICS topology)
- date-fns + lucide-react

## Features

- Secure login with token persistence
- Protected routes with role checks
- OT dashboard: KPIs, sensor charts, alert trends
- Asset registry + filters + detail page
- ICS topology graph with status-aware nodes and edges
- Alert operations with drawer (acknowledge/resolve + MITRE mapping)
- Collector monitoring
- Admin users management
- Toast notifications
- Dark industrial UI

## Project Structure

See requested architecture under `src/`:
- `api/`, `hooks/`, `store/`, `constants/`
- `components/layout`, `components/ui`, `components/charts`, `components/topology`, `components/alerts`
- `pages/`
- `router/ProtectedRoute.jsx`

## Environment

Create `.env` from example:

```bash
cp .env.example .env
```

Required variable:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Install & Run

```bash
npm install
npm run dev
```

Build:

```bash
npm run build
npm run preview
```

Lint:

```bash
npm run lint
```

## Backend expectations

Backend base URL:
- `http://localhost:8000/api/v1`

Auth endpoints should provide:
- access token
- refresh token
- user object

## Notes

- `public/favicon.svg` can be replaced with branded industrial shield/gear icon.
- Sidebar is collapsible on desktop and compatible with mobile breakpoints.
- All major pages implement loading/empty/error-tolerant rendering patterns.
