# Vertex Tech Store

Tienda web full-stack de Vertex Coders LLC — FastAPI + single-file HTML + PWA, **multitenant desde la base**.

## Stack
- **Backend:** FastAPI · Pydantic v2 · Python 3.11 · `lru_cache` para el catálogo CSV
- **IA:** OpenAI / Anthropic con **fallback local por reglas** (sin coste, sin API key)
- **Frontend:** HTML + Tailwind Play CDN + Inter + Lucide (single-file)
- **PWA:** manifest + service worker (precache, network-first API, cache-first assets)
- **Deploy:** Docker multi-stage (non-root + HEALTHCHECK) · docker-compose (API + Nginx) · Railway · Fly.io · Netlify
- **Tenancy:** middleware `TenantMiddleware` (header `X-Tenant-ID` / subdominio)

## Arranque rápido
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload          # → http://localhost:8000  (docs: /docs)

# Frontend (en otra terminal, desde la raíz)
python -m http.server 5500         # → http://localhost:5500
# o con Docker:
docker compose up --build          # → http://localhost:8080 (frontend) + :8000 (API)
```

## Endpoints
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Info del servicio |
| GET | `/health` | Healthcheck (estado del CSV) |
| GET | `/products` | Catálogo desde `productos.csv` (caché) |
| POST | `/chat` | Chat IA `{message}` → `{reply, provider}` |

## Multitenant
Ver `docs/MULTITENANT.md`. Resumen:
- Todo request pasa por `TenantMiddleware` → `request.state.tenant` (devuelto también en header `X-Tenant-ID`).
- Resolución: header `X-Tenant-ID` > subdominio `{tenant}.midominio.com` > `public`.
- La Fase MT-2 migrará el catálogo CSV a Postgres con `tenant_id` + Row-Level Security.

## Seguridad
Headers CSP/HSTS/nosniff en `_headers` y `nginx.conf`. CORS permisivo solo para desarrollo.

## Licencia
MIT © Vertex Coders LLC
