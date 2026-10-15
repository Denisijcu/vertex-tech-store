"""Núcleo de IA de Vertex Coders (sitio de servicios).

Proveedores, en orden con AI_PROVIDER=auto:
  1. huggingface  -> Hugging Face Inference Providers (router OpenAI-compatible)
  2. openai
  3. anthropic
  4. local        -> fallback por reglas, sin red y sin coste (siempre disponible)

Configuración 100% por variables de entorno. Los SDK se importan de forma lazy.
"""
from __future__ import annotations

import logging
import os
import random
import re
from typing import List, Optional, Tuple

logger = logging.getLogger("vertex-ai")


def _env(name: str, default: str = "") -> str:
    """Lee una variable de entorno tolerando comentarios inline (`valor  # comentario`)."""
    raw = os.getenv(name, default) or default
    return raw.split("#", 1)[0].strip().strip('"').strip("'")


# ── Configuración ──────────────────────────────────────────
AI_PROVIDER = _env("AI_PROVIDER", "auto").lower()  # auto | huggingface | openai | anthropic | local
AI_TIMEOUT_S = float(_env("AI_TIMEOUT_S", "30") or 30)
AI_MAX_TOKENS = int(_env("AI_MAX_TOKENS", "400") or 400)

HF_TOKEN = _env("HF_TOKEN") or _env("HUGGINGFACE_HUB_TOKEN")
HF_BASE_URL = _env("HF_BASE_URL", "https://router.huggingface.co/v1")
HF_MODEL = _env("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_MODEL = _env("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = _env("ANTHROPIC_MODEL", "claude-haiku-5-5")

CONTACT_HINT = "Escríbenos por WhatsApp con el botón «Negociar / Contactar» y lo concretamos."

# ── Fallback local por intenciones (sitio de servicios) ────
KEYWORDS = {
    "precio": ("precio", "costo", "cuesta", "cuánto", "cuanto", "presupuesto", "tarifa", "cotiz"),
    "ia": ("ia", "agente", "llm", "modelo", "fine", "qlora", "unsloth", "mcp", "chatbot", "rag"),
    "web": ("web", "página", "pagina", "fullstack", "full stack", "api", "fastapi", "backend", "base de datos"),
    "movil": ("android", "app", "móvil", "movil", "compose", "kotlin"),
    "seguridad": ("seguridad", "ciber", "pentest", "htb", "hackthebox", "auditor"),
    "libro": ("libro", "kdp", "amazon", "editorial", "publicar"),
    "pago": ("pago", "pagar", "transferencia", "cripto", "factura"),
    "entrega": ("entrega", "plazo", "tiempo", "cuándo", "cuando", "demora", "soporte"),
}

LOCAL_RESPONSES = {
    "precio": "Los precios del catálogo son tarifas de referencia; el costo final depende del alcance. " + CONTACT_HINT,
    "ia": "Hacemos fine-tuning de modelos propios (QLoRA/Unsloth), servidores MCP y agentes IA autónomos con guardrails de seguridad. " + CONTACT_HINT,
    "web": "Desarrollamos plataformas web full stack y APIs de alto rendimiento con FastAPI/NestJS y bases de datos. " + CONTACT_HINT,
    "movil": "Creamos apps Android nativas con Kotlin y Jetpack Compose. " + CONTACT_HINT,
    "seguridad": "Ofrecemos herramientas de ciberseguridad y máquinas virtuales tipo HackTheBox. " + CONTACT_HINT,
    "libro": "Te ayudamos a crear y publicar literatura técnica en Amazon KDP. " + CONTACT_HINT,
    "pago": "Trabajamos con transferencias, criptomonedas y pasarelas internacionales según el acuerdo. " + CONTACT_HINT,
    "entrega": "Los plazos se definen según el alcance del proyecto e incluyen soporte especializado de Vertex Coders LLC. " + CONTACT_HINT,
    "default": "¡Hola! Soy Vertex Core AI. Te ayudo con nuestros servicios de IA, desarrollo web y móvil, ciberseguridad y publicación técnica. ¿Qué necesitas?",
}


CONTACT_HINT_EN = "Message us on WhatsApp with the «Negotiate / Contact» button and we'll sort out the details."

LOCAL_RESPONSES_EN = {
    "precio": "Catalog prices are reference rates; the final cost depends on scope. " + CONTACT_HINT_EN,
    "ia": "We fine-tune custom models (QLoRA/Unsloth), build MCP servers and autonomous AI agents with security guardrails. " + CONTACT_HINT_EN,
    "web": "We build full stack web platforms and high-performance APIs with FastAPI/NestJS and databases. " + CONTACT_HINT_EN,
    "movil": "We build native Android apps with Kotlin and Jetpack Compose. " + CONTACT_HINT_EN,
    "seguridad": "We offer cybersecurity tooling and HackTheBox-style virtual machines. " + CONTACT_HINT_EN,
    "libro": "We help you write and publish technical books on Amazon KDP. " + CONTACT_HINT_EN,
    "pago": "We accept bank transfers, crypto and international payment gateways, per agreement. " + CONTACT_HINT_EN,
    "entrega": "Timelines depend on project scope and include specialized support from Vertex Coders LLC. " + CONTACT_HINT_EN,
    "default": "Hi! I'm Vertex Core AI. I can help with our AI, web and mobile development, cybersecurity and technical publishing services. What do you need?",
}

# Palabras clave en inglés para el clasificador local
KEYWORDS_EN = {
    "precio": ("price", "cost", "how much", "quote", "rate", "budget"),
    "ia": ("ai", "agent", "llm", "model", "fine", "qlora", "mcp", "chatbot", "rag"),
    "web": ("web", "website", "fullstack", "full stack", "api", "backend", "database"),
    "movil": ("android", "app", "mobile", "compose", "kotlin"),
    "seguridad": ("security", "cyber", "pentest", "htb", "hackthebox", "audit"),
    "libro": ("book", "kdp", "amazon", "publish"),
    "pago": ("pay", "payment", "transfer", "crypto", "invoice"),
    "entrega": ("delivery", "timeline", "deadline", "when", "support"),
}


def _classify(message: str) -> str:
    text = message.lower()
    tokens = set(re.findall(r"[a-záéíóúñü]+", text))
    for intent in KEYWORDS:
        for w in KEYWORDS[intent] + KEYWORDS_EN.get(intent, ()):
            # palabras cortas: coincidencia exacta (evita que "ia" matchee "garantía");
            # frases o palabras largas: subcadena (permite "cotiz" -> "cotización")
            if w in tokens or ((" " in w or len(w) > 4) and w in text):
                return intent
    return "default"


def _clean(text: str) -> str:
    """Quita bloques de razonamiento (<think>…</think>) que algunos modelos devuelven."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    # Red de seguridad por si el modelo ignora la regla de "sin Markdown"
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)                 # **negrita**
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)   # # encabezados
    text = re.sub(r"^\s*[\*\-]\s+", "• ", text, flags=re.MULTILINE)  # * item / - item
    text = re.sub(r"\s+\*\s+(?=\S)", "\n• ", text)                # lista * en línea
    return text.strip()


def _build_messages(system_prompt: str, user_message: str, history: Optional[List[dict]]) -> List[dict]:
    msgs = [{"role": "system", "content": system_prompt}]
    for turn in (history or [])[-10:]:
        role = turn.get("role")
        content = str(turn.get("content", ""))[:2000]
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": user_message})
    return msgs


# ── Proveedores remotos ────────────────────────────────────
async def _openai_compatible(base_url: Optional[str], api_key: str, model: str, messages: List[dict]) -> str:
    from openai import AsyncOpenAI  # lazy import
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=AI_TIMEOUT_S, max_retries=1)
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=AI_MAX_TOKENS,
        temperature=0.4,
    )
    reply = _clean(resp.choices[0].message.content or "")
    if not reply:
        raise RuntimeError("respuesta vacía del modelo")
    return reply


async def _anthropic_reply(system_prompt: str, messages: List[dict]) -> str:
    import anthropic  # lazy import
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, timeout=AI_TIMEOUT_S, max_retries=1)
    resp = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=AI_MAX_TOKENS,
        system=system_prompt,
        messages=[m for m in messages if m["role"] != "system"],
    )
    reply = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
    reply = _clean(reply)
    if not reply:
        raise RuntimeError("respuesta vacía del modelo")
    return reply


async def _local_reply(message: str, lang: str = "es") -> str:
    intent = _classify(message)
    if lang == "en":
        return LOCAL_RESPONSES_EN[intent]
    reply = LOCAL_RESPONSES[intent]
    if intent == "default" and len(message) > 3:
        reply += " " + random.choice((
            "Cuéntame un poco de tu proyecto y te oriento.",
            "¿Buscas IA, web, móvil o ciberseguridad?",
        ))
    return reply


def active_providers() -> List[str]:
    """Proveedores remotos configurados (para /health)."""
    out = []
    if HF_TOKEN:
        out.append("huggingface")
    if OPENAI_API_KEY:
        out.append("openai")
    if ANTHROPIC_API_KEY:
        out.append("anthropic")
    return out


# ── API pública ────────────────────────────────────────────
async def invoke_ai(user_message: str, system_prompt: str,
                    history: Optional[List[dict]] = None, lang: str = "es") -> Tuple[str, str]:
    """Devuelve (respuesta, proveedor). Nunca lanza: si todo falla, usa el fallback local."""
    messages = _build_messages(system_prompt, user_message, history)
    order = ["huggingface", "openai", "anthropic"] if AI_PROVIDER == "auto" else [AI_PROVIDER]

    for provider in order:
        try:
            if provider == "huggingface" and HF_TOKEN:
                return await _openai_compatible(HF_BASE_URL, HF_TOKEN, HF_MODEL, messages), "huggingface"
            if provider == "openai" and OPENAI_API_KEY:
                return await _openai_compatible(None, OPENAI_API_KEY, OPENAI_MODEL, messages), "openai"
            if provider == "anthropic" and ANTHROPIC_API_KEY:
                return await _anthropic_reply(system_prompt, messages), "anthropic"
        except Exception as exc:  # un proveedor caído no tumba el chat
            logger.warning("proveedor %s falló: %s", provider, exc)

    return await _local_reply(user_message, lang), "local"
