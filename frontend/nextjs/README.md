# Predicast Frontend (Next.js skeleton)

This is a minimal Next.js skeleton intended to be the starting point for the Next.js frontend described in the architecture plan.

Local development:

```bash
cd 07_Sistema_Produccion/frontend/nextjs
npm install
npm run dev
```

Build & run (production):

```bash
npm run build
npm start
```

Docker build:

```bash
docker build -t predicast-frontend:local .
docker run -p 3000:3000 predicast-frontend:local
```

The frontend expects the API to be available at the same origin under `/api/v1/*` (FastAPI in `07_Sistema_Produccion/src/main.py`).
