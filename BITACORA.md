# Vertex Coders — Página de servicios (vertex-tech-store) — Bitácora

**Qué es:** la web pública donde Vertex Coders LLC ofrece sus servicios (IA, agentes, MCP, web,
Android, ciberseguridad, publicación técnica), con un asistente IA (Vertex Core AI) que atiende a
los clientes y los lleva a WhatsApp. No es una tienda: el nombre del repo viene del primer prompt.

Ruta: G:\vertex-tech-store
Producción:
- Dominio propio: https://vertex-services.org (comprado el 14/10/2026 por $11.99; www y http redirigen al apex con HTTPS)
- Frontend: Netlify (vertex-tech-store.netlify.app), despliega solo al hacer push a GitHub
- Backend: https://denisijcu-vertex-tech-store-api.hf.space (Hugging Face Space, Docker, puerto 7860)

## 2026-10-14 (tarde) — El Plan Maestro v2

- Revisado el prompt original (F:\Plan_Maestro\Prompt Maestro para el Generador de Pagina Web.txt).
  Buena base (rol, design system, secciones), pero con huecos: /chat sin contrato, imágenes de
  example.com (404), testimonio inventado de una persona real, Tailwind Play CDN vendido como
  producción, formulario y carrito sin función, sin footer/SEO/accesibilidad/README serio.
- Escrito "Plan Maestro v2 - Generador Web Fullstack Vertex.md": Parte A fija (constitución de
  calidad) + Parte B de variables por cliente. Decisión: a partir de ahora se sigue la v2.

## 2026-10-14 (noche) — Chatbot conectado y página de servicios en producción

### Diagnóstico: el chat nunca llegaba a un modelo
- Prueba en vivo contra el Space: `provider: "local"`, o sea, siempre el fallback por reglas.
- Causa 1: main.py no cargaba el .env (faltaba python-dotenv) → en local las keys llegaban vacías.
- Causa 2: AI_PROVIDER tenía el comentario pegado (`auto # auto | openai | ...`, 49 caracteres) →
  nunca era igual a "auto".
- Causa 3: el system prompt era de la tienda de hardware (envíos, devoluciones, Stripe): le habría
  dicho falsedades a los clientes.

### Backend (backend\ai_core.py reescrito, backend\main.py)
- Orden de proveedores con AI_PROVIDER=auto: huggingface → openai → anthropic → local.
- Hugging Face por el router OpenAI-compatible https://router.huggingface.co/v1 con HF_TOKEN
  (token fine-grained con permiso "Make calls to Inference Providers"). Modelo por defecto:
  meta-llama/Llama-3.3-70B-Instruct (cambiable con HF_MODEL).
- _env() tolera comentarios inline en el .env. load_dotenv antes de importar ai_core.
- System prompt nuevo de servicios: tarifas "de referencia", contratación por WhatsApp, no inventar
  precios/plazos/garantías, solo temas de Vertex, resistir instrucciones que intenten cambiar reglas.
- /chat acepta `history` (últimos 10 turnos) y `lang` (es|en). /health informa `ai_providers`.
- Respuestas en texto plano con viñetas "•"; _clean() quita <think>, **negrita**, # y listas "*".
- Con lang=en se le pasa al modelo el catálogo ya en inglés (sin eso dejaba los nombres en español).
- Fallback local reescrito para servicios, en español e inglés.
- requirements.txt: añadido python-dotenv. .env.example con las variables de HF.
- backend\Dockerfile (el de docker-compose local): quitada la línea `COPY ../productos.csv ... || true`,
  que rompía el build. El Space usa su propio Dockerfile en la raíz (copia backend/, puerto 7860).

### Frontend (index.html)
- Toda la página pasó de "tienda de hardware" a servicios: hero "Ingeniería de IA de Élite",
  stats verificables (B2B · IA privada · Directo) en vez de "24/7 / 99.9% / Envíos globales".
- Testimonios inventados (incluido el de Musk) sustituidos por "Trayectoria" con trabajo real:
  libros en Amazon, modelo Vertex-Core, SaaS de contabilidad en producción, HTB/SOC/OSINT.
  Motivo: la regla de la FTC (16 CFR 465) prohíbe testimonios falsos.
- Indicador "En línea" real: consulta GET /health (verde En línea / ámbar Despertando…).
- Chat: respuesta con textContent (nunca innerHTML), historial, timeout de 60 s (el Space dormido
  tarda en despertar), botón bloqueado mientras espera, Esc para cerrar, foco devuelto al cerrar.
- Bilingüe ES/EN con selector propio; idioma por ?lang= > elección guardada > navegador.
  `translate="no"` para que Chrome no meta su traducción automática.
- Precios como "Desde $X"; tarjeta de WhatsApp en contacto (las redes apuntaban a "#").
- Accesibilidad: aria en FAQ y chat, "Saltar al contenido", foco visible, prefers-reduced-motion.
- manifest.json con el nombre Vertex Coders y el atajo /#servicios.

### Netlify (netlify.toml)
- publish = "." servía el código del backend como archivos públicos → /backend/* y /docs/* → 404.
- Reactivado el escáner de secretos (estaba SECRETS_SCAN_ENABLED = "false").

### Verificado en producción
- /health del Space: ai_providers = [huggingface, anthropic].
- /chat en inglés y en español: provider huggingface, lista limpia, nombres en el idioma correcto.
- La página en Netlify muestra "Online" y el selector ES/EN funciona.

### Pendientes
- OpenAI falla en local (probablemente key vencida o sin crédito): mirar el WARNING en uvicorn.
- .gitignore tiene `.env.*`, que también ignora .env.example (que sí debería subirse).
- Confirmar email y teléfono de contacto; añadir URLs reales de GitHub/LinkedIn.
- Testimonios reales de clientes, solo con permiso por escrito.
- Producción "de verdad": pasar de Tailwind Play CDN a Tailwind CLI y fijar la versión de Lucide.

## 2026-10-14 (noche) — Protocolo de cierre

- Bitácora al día (este archivo).
- Video promo: F:\vertex-videos\vertex_tech_store.py, escena VertexTechStorePromo (~67 s, 10 partes:
  diagnóstico, ruta de una pregunta, cadena de respaldo, reglas, bilingüe, prueba social honesta,
  seguridad del deploy, cifras, cierre). Render de prueba en 480p revisado por fotogramas; render
  final: `venv\Scripts\manim.exe -qh vertex_tech_store.py VertexTechStorePromo` desde F:\vertex-videos.
- Libro: plan e índice en F:\vertex-tech-store-libro\PLAN.md ("De prompt a producción"); manuscrito en marcha.

## 2026-10-14 (noche) — Dominio propio: vertex-services.org

- Denis compró vertex-services.org ($11.99) y lo apuntó a Netlify.
- Verificado: https 200; www.vertex-services.org y http:// redirigen a https://vertex-services.org/;
  /backend/main.py devuelve 404 también en el dominio nuevo.
- index.html: canonical, og:url y hreflang (es, en, x-default) apuntando al dominio.
- El backend no necesitó cambios: ALLOWED_ORIGINS sigue en "*" (sin credenciales). Si se
  restringe, poner https://vertex-services.org y http://localhost:5500.
- Video: el cierre ahora muestra vertex-services.org. Render final 1080p60 listo y revisado:
  F:\vertex-videos\media\videos\vertex_tech_store\1080p60\VertexTechStorePromo.mp4 (3.8 MB, ~67 s).
- Libro: primer borrador completo del manuscrito en F:\vertex-tech-store-libro\manuscrito (11 capítulos,
  conclusión, 3 apéndices, sobre el autor); build scripts adaptados. Falta generar EPUB/PDF, portada y ficha KDP.
