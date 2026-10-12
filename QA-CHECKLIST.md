# QA Checklist — Fase 1

## Backend
- [ ] `GET /health` → 200 `{ok, status, csv}`
- [ ] `GET /products` → 5 productos tipados
- [ ] CSV faltante → 500 JSON limpio (sin stacktrace)
- [ ] `POST /chat` con mensaje válido → respuesta + provider
- [ ] `POST /chat` con mensaje vacío → 422
- [ ] Header `X-Tenant-ID: acme` → respuesta incluye `X-Tenant-ID: acme`

## Frontend
- [ ] Navbar sticky + menú hamburguesa móvil
- [ ] Skeleton loaders → productos → precios formateados USD
- [ ] Error state con botón reintentar (backend caído)
- [ ] Botón "Agregar al carrito" → verde + check 1.6s
- [ ] FAQ: solo uno abierto, icono rota 45°
- [ ] Chatbot: bootstrap, typing indicator, errores de red
- [ ] Footer con año dinámico

## PWA
- [ ] `manifest.json` válido (Lighthouse PWA)
- [ ] SW: precache en install, limpieza en activate
- [ ] API offline → 503 JSON

## Performance / Seguridad
- [ ] Lighthouse ≥ 90
- [ ] Headers CSP/HSTS presentes
