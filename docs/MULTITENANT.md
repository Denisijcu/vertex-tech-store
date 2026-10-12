# Arquitectura Multitenant — Vertex Tech Store

Objetivo: una única instancia del código sirve **N tiendas** aisladas entre sí.

## 1. Modelo de tenancy
| Decisión | Elección | Por qué |
|---|---|---|
| Aislamiento | **Shared schema + `tenant_id` + Postgres RLS** | Balance entre coste, operación simple y seguridad real (RLS a nivel de fila, a prueba de bugs de aplicación) |
| Resolución de tenant | Header `X-Tenant-ID` > subdominio `{tenant}.dominio.com` > `public` | Flexible para API, web y dev local |
| Identidad admin | JWT con claim obligatorio `tid` (tenant id) | Un admin nunca puede cruzar tenants |
| Catálogo fase actual | CSV compartido (tenant `public`) | Fase 1; se migra en MT-2 |

## 2. Fundamento ya implementado (Fase 1 ✅)
- `backend/tenancy.py` → `TenantMiddleware` inyecta `request.state.tenant` y devuelve header `X-Tenant-ID` en cada respuesta.
- Regla global para todo módulo futuro: **ningún modelo de datos se crea sin `tenant_id`** y **ningún query sin filtro de tenant**.

## 3. Fases de implementación
| Fase | Alcance |
|---|---|
| **MT-1 (ahora)** | Middleware + resolución + logging por tenant + documentación |
| **MT-2** | Migrar `productos.csv` → Postgres; `products.tenant_id` + RLS; seed por tenant; admin CRUD por tenant |
| **MT-3** | JWT con `tid`; `require_admin` valida claim; onboarding de tenants (crear tenant = migración de schema + seed) |
| **MT-4** | Multi-tenant en el resto del plan: órdenes, suscriptores, blog, campañas, analytics, A/B tests (todos con `tenant_id`) |
| **MT-5** | Aislamiento de datos sensibles: backups por tenant, límites de cuota por plan (free/pro), dominios personalizados por tenant |

## 4. Reglas duras (aplicables desde ya)
1. Toda tabla nueva lleva `tenant_id TEXT NOT NULL` + índice compuesto `(tenant_id, ...)`.
2. Toda query pasa por el ORM/función central `scoped(tenant)` — nunca SQL crudo sin filtro.
3. El claim `tid` del JWT debe coincidir con el tenant resuelto del request → mismatch = 403.
4. Eventos de analytics incluyen `tenant_id` para dashboards por tienda.
5. Tests: siempre correr la suite con 2 tenants y verificar que A no ve datos de B (test de fuga).

## 5. Migración CSV → Postgres (MT-2, preview)
```sql
CREATE TABLE products (
  id          SERIAL PRIMARY KEY,
  tenant_id   TEXT NOT NULL DEFAULT 'public',
  name        TEXT NOT NULL,
  price       NUMERIC(10,2) NOT NULL CHECK (price >= 0),
  category    TEXT NOT NULL,
  image_url   TEXT NOT NULL
);
CREATE INDEX idx_products_tenant ON products(tenant_id, id);

ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON products
  USING (tenant_id = current_setting('app.tenant_id', TRUE));
```
El backend ejecuta `SET app.tenant_id = '<tenant resuelto>'` por conexión/request.
