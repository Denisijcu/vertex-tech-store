"""
Vertex Tech Store API — FastAPI (production-ready, tenant-aware con catálogo en memoria).
"""
from __future__ import annotations

import logging
import os
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ai_core import invoke_ai
from tenancy import TenantMiddleware

# ── Logging estructurado ───────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("vertex-api")

app = FastAPI(title="Vertex Tech Store API", version="1.0.0")

# CORS permisivo para desarrollo y producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)  # multitenant desde la base

# ── Modelos Pydantic v2 ────────────────────────────────────
class Product(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=120)
    price: float = Field(ge=0)
    category: str = Field(min_length=1, max_length=60)
    image_url: str = Field(min_length=1, max_length=500)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

class ChatResponse(BaseModel):
    reply: str
    provider: str

# ── Catálogo en Memoria (Bypasseando la dependencia de CSV) ──
PRODUCTS_DB: List[Product] = [
    Product(
        id=1,
        name="Afinamiento de Modelos LM (QLoRA/Unsloth)",
        price=1499.99,
        category="IA & Agentes",
        image_url="https://plus.unsplash.com/premium_photo-1683120963435-6f9355d4a776?q=80&w=726&auto=format&fit=crop"
    ),
    Product(
        id=2,
        name="Arquitectura de Servidores MCP (Model Context Protocol)",
        price=1199.99,
        category="IA & Agentes",
        image_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=500&auto=format&fit=crop"
    ),
    Product(
        id=3,
        name="Desarrollo de Agentes IA Autónomos",
        price=1899.99,
        category="IA & Agentes",
        image_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=500&auto=format&fit=crop"
    ),
    Product(
        id=4,
        name="Plataformas Web Full Stack & Bases de Datos",
        price=899.99,
        category="Backend & Web",
        image_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=500&auto=format&fit=crop"
    ),
    Product(
        id=5,
        name="Desarrollo de Apps Android (Jetpack Compose)",
        price=1299.99,
        category="Mobile Apps",
        image_url="https://images.unsplash.com/photo-1607252650355-f7fd0460ccdb?q=80&w=500&auto=format&fit=crop"
    ),
    Product(
        id=6,
        name="Ingeniería de APIs de Alto Rendimiento (FastAPI/NestJS)",
        price=799.99,
        category="Backend & Web",
        image_url="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=500&auto=format&fit=crop"
    ),
    Product(
        id=7,
        name="Herramientas de Ciberseguridad & Máquinas Virtuales HTB",
        price=1599.99,
        category="Ciberseguridad",
        image_url="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=500&auto=format&fit=crop"
    ),
    Product(
        id=8,
        name="Creación de Literatura Técnica y Publicación KDP",
        price=2499.99,
        category="Editorial & Tech",
        image_url="https://images.unsplash.com/photo-1532012197267-da84d127e765?q=80&w=500&auto=format&fit=crop"
    ),
    Product(
        id=9,
        name="Arquitecto de IA Senior & Contractor Externo (Remoto B2B)",
        price=3500.00,
        category="Consultoría Elite",
        image_url="https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=500&auto=format&fit=crop"
    )
]

def get_products() -> List[Product]:
    return PRODUCTS_DB

# ── Handlers globales de error ─────────────────────────────
@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"ok": False, "error": exc.detail})

@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    logger.exception("Error no controlado en %s", request.url.path)
    return JSONResponse(status_code=500,
                        content={"ok": False, "error": "internal_error"})

# ── Endpoints ──────────────────────────────────────────────
@app.get("/")
async def root():
    return {"ok": True, "service": "vertex-tech-store-api", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"ok": True, "status": "healthy", "catalog_items": len(PRODUCTS_DB)}

@app.get("/products", response_model=List[Product])
async def products(request: Request):
    logger.info("tenant=%s solicitó el catálogo en memoria", request.state.tenant)
    return get_products()

@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    try:
        # 1. Obtenemos los productos directos del arreglo
        products_list = get_products()
        
        # 2. Construimos un resumen del catálogo para la IA
        catalog_context = "Catálogo de productos de Vertex Tech Store:\n"
        for p in products_list:
            catalog_context += f"- ID: {p.id} | {p.name} | Categoría: {p.category} | Precio: ${p.price:.2f}\n"
        
        # 3. Definimos las reglas del asistente y el contexto de la tienda
        system_prompt = (
            "Eres 'Vertex Core AI', el asistente virtual experto y oficial de Vertex Tech Store, "
            "una tienda de hardware de élite creada por Vertex Coders LLC.\n"
            "Responde de forma profesional, directa y cercana."
            "Usa la siguiente información del catálogo para responder dudas sobre precios, stock o modelos:\n\n"
            f"{catalog_context}\n"
            "Información general de envíos y políticas:\n"
            "- Envíos: Entre 2 y 5 días hábiles. Gratis en pedidos desde $50.\n"
            "- Garantía: 12 meses de cobertura total contra defectos de fabricación.\n"
            "- Devoluciones: 30 días para devoluciones sin preguntas.\n"
            "- Pagos: Tarjetas, Apple Pay y Google Pay mediante Stripe.\n"
        )
        
        # 4. Combinamos el prompt del sistema con el mensaje del cliente
        full_prompt = f"{system_prompt}\n\nPregunta del cliente: {payload.message}"
        
        reply, provider = await invoke_ai(full_prompt)
        logger.info("chat tenant=%s provider=%s", request.state.tenant, provider)
        return ChatResponse(reply=reply, provider=provider)
    except Exception:
        logger.exception("Error en /chat")
        raise HTTPException(status_code=500, detail="El asistente no está disponible")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)