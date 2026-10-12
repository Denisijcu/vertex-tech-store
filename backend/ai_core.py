"""Núcleo de IA para Vertex Tech Store.

Soporta OpenAI, Anthropic y un fallback local por reglas.
Los SDKs se importan de forma lazy para no romper el arranque
si no están instalados. Configuración 100% por variables de entorno.
"""
from __future__ import annotations

import logging
import os
import random
from typing import Tuple

logger = logging.getLogger("vertex-ai")

# ── Configuración por entorno ──────────────────────────────
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto").lower()  # auto | openai | anthropic | local
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

SYSTEM_PROMPT = (
    "Eres 'Vertex Core AI', el asistente virtual de Vertex Tech Store. "
    "Respondes en español, de forma breve, útil y orientada a la conversión. "
    "Ayudas con productos de hardware, envíos, garantías y pedidos."
)

# ── Clasificador local por intenciones (fallback sin coste) ─
KEYWORDS = {
    "envio": ("envío", "envio", "shipping", "entrega", "demora", "llega", "courier"),
    "garantia": ("garantía", "garantia", "devolución", "devolucion", "reembolso", "warranty"),
    "precio": ("precio", "costo", "cuánto", "cuanto", "descuento", "oferta", "promoción", "promocion"),
    "pago": ("pago", "tarjeta", "stripe", "paypal", "factura", "checkout"),
    "producto": ("mouse", "teclado", "monitor", "audífono", "audifono", "headset", "adapter", "adaptador", "rgb"),
}

LOCAL_RESPONSES = {
    "envio": "🚚 Realizamos envíos express a todo el mundo. En pedidos superiores a $50 el envío es **gratis**; de lo contrario, tarifa plana de $9.95. Entrega estimada: 2-5 días hábiles.",
    "garantia": "🛡️ Todos nuestros productos incluyen la **Garantía Vertex** de 12 meses contra defectos de fabricación. Si algo falla, te lo reemplazamos sin preguntas.",
    "precio": "💰 Tenemos precios competitivos y envío gratis desde $50. ¿Buscas algo específico? Puedo orientarte con el catálogo.",
    "pago": "💳 Aceptamos tarjetas de crédito/débito, Apple Pay y Google Pay a través de Stripe, con procesamiento 100% seguro y cifrado.",
    "producto": "🖥️ Contamos con periféricos de élite: mouse ergonómico inalámbrico ($29.99), teclado mecánico RGB ($89.50), monitor ultrawide 29\" ($249.99), headset con cancelación de ruido ($120.00) y adaptador USB-C multipuerto ($35.49).",
    "default": "¡Hola! 👋 Soy Vertex Core AI. Puedo ayudarte con productos, envíos, garantías y pagos. ¿Qué necesitas?",
}

def _classify(message: str) -> str:
    text = message.lower()
    for intent, words in KEYWORDS.items():
        if any(w in text for w in words):
            return intent
    return "default"

# ── Providers remotos ──────────────────────────────────────
async def _openai_reply(message: str) -> str:
    from openai import AsyncOpenAI  # lazy import
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        max_tokens=300,
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()

async def _anthropic_reply(message: str) -> str:
    import anthropic  # lazy import
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    resp = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
    )
    
    # Extraemos el texto de forma segura recorriendo los bloques de contenido
    reply_text = ""
    for block in resp.content:
        if hasattr(block, "text") and getattr(block, "type", "text") == "text":
            reply_text += block.text
            
    return reply_text.strip()

async def _local_reply(message: str) -> str:
    """Fallback local: sin coste, sin red, siempre disponible."""
    intent = _classify(message)
    reply = LOCAL_RESPONSES[intent]
    if intent == "default" and len(message) > 3:
        greetings = ("¡Perfecto! Cuéntame más para ayudarte mejor.",
                     "Entendido. ¿Sobre qué producto o tema te gustaría saber más?",
                     "Claro. Nuestro equipo también puede asistirte por email o chat.")
        reply = f"{reply} {random.choice(greetings)}"
    return reply

# ── API pública del módulo ─────────────────────────────────
async def invoke_ai(user_message: str) -> Tuple[str, str]:
    """Devuelve (respuesta, proveedor_usado). Nunca lanza excepción
    al caller: si todo falla, usa el fallback local."""
    order = ["openai", "anthropic"] if AI_PROVIDER == "auto" else [AI_PROVIDER]
    for provider in order:
        try:
            if provider == "openai" and OPENAI_API_KEY:
                return await _openai_reply(user_message), "openai"
            if provider == "anthropic" and ANTHROPIC_API_KEY:
                return await _anthropic_reply(user_message), "anthropic"
        except Exception as exc:  # un proveedor caído no tumba el chat
            logger.warning("proveedor %s falló: %s", provider, exc)
    reply = await _local_reply(user_message)
    return reply, "local"
