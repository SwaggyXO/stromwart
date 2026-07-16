# Stromwart Frontend

React + TypeScript + Vite SPA for the Stromwart QoE Intelligence Platform.

## Stack

| Layer | Tech |
|---|---|
| Framework | React 18 + TypeScript |
| Build | Vite 5 |
| State | Zustand |
| Auth | Auth0 (`@auth0/auth0-react`) |
| Design System | [Astryx](https://astryx.atmeta.com) (`@astryxdesign/core` + `theme-gothic`) |
| Charts | Chart.js + react-chartjs-2 |
| Routing | React Router v6 |
| Icons | Lucide React |

## Quick start

```bash
cd frontend
npm install
cp .env.example .env.local
# Fill in VITE_AUTH0_DOMAIN and VITE_AUTH0_CLIENT_ID
npm run dev
```

## Auth0 setup

1. Create a Single-Page Application in Auth0 dashboard
2. Set **Allowed Callback URLs**: `http://localhost:3000`
3. Set **Allowed Logout URLs**: `http://localhost:3000/login`
4. Set **Allowed Web Origins**: `http://localhost:3000`
5. Copy Domain + Client ID into `.env.local`

## Pages

| Route | Page | Description |
|---|---|---|
| `/login` | Login | Auth0 SSO entry point |
| `/` | Live Event | KPI dashboard + forecast chart + incidents + alerts + session table |
| `/incidents/:id` | Incident Detail | Hypothesis, evidence, proposal, guardrail state, operator actions |
| `/audit` | Audit Log | Append-only record of all system/agent/operator events |

## Deploy to Vercel

```bash
npm run build
# Point Vercel root to frontend/, output dir to dist/
# Add VITE_AUTH0_DOMAIN and VITE_AUTH0_CLIENT_ID as env vars
```

## Guardrail states

Every action proposal has a `policy_state` from the deterministic policy verifier:

`OBSERVE` → `INVESTIGATE` → `RECOMMEND` → `SIMULATE` → `APPROVE_REQUIRED` → `BLOCKED`
