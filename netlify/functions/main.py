"""Vertex Tech Store API — FastAPI (production-ready, tenant-aware)."""
from __future__ import annotations

import csv
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from fastapi import Depends, FastAPI, HTTPException, Request
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

BASE_DIR = Path(__file__).parent.parent  # raíz del proyecto
CSV_PATH = Path(os.getenv("PRODUCTS_CSV", BASE_DIR / "productos.csv"))

app = FastAPI(title="Vertex Tech Store API", version="1.0.0")

# CORS permisivo para desarrollo (restringir en producción)
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

# ── Lectura eficiente del CSV con caché ────────────────────
@lru_cache(maxsize=4)
def _read_products(path_str: str) -> Tuple[Product, ...]:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {path}")
    products: List[Product] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            products.append(Product(
                id=int(row["id"]),
                name=row["name"].strip(),
                price=float(row["price"]),
                category=row["category"].strip(),
                image_url=row["image_url"].strip(),
            ))
    return tuple(products)

def get_products() -> List[Product]:
    try:
        return list(_read_products(str(CSV_PATH)))
    except FileNotFoundError as exc:
        logger.error("Catálogo no disponible: %s", exc)
        raise HTTPException(status_code=500, detail="Catálogo no disponible temporalmente")
    except (ValueError, KeyError):
        logger.exception("CSV corrupto o con formato inválido")
        raise HTTPException(status_code=500, detail="Error interno del catálogo")

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
    csv_ok = CSV_PATH.exists()
    return {"ok": True, "status": "healthy" if csv_ok else "degraded", "csv": csv_ok}

@app.get("/products", response_model=List[Product])
async def products(request: Request):
    # Fase MT-2: filtrar por request.state.tenant cuando el catálogo sea multi-tenant
    logger.info("tenant=%s solicitó el catálogo", request.state.tenant)
    return get_products()

@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    try:
        # 1. Obtenemos los productos actuales del CSV
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
        
        # 4. Combinamos el prompt del sistema con el mensaje del usuario 
        # (Asegúrate de que tu función invoke_ai acepte un system prompt o un historial/mensajes, 
        # o puedes anteponérselo al mensaje según cómo tengas estructurado ai_core).
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
