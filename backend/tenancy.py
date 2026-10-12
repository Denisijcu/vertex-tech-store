"""Resolución de tenant (FUNDAMENTO MULTITENANT — Fase 1).

Estrategia de resolución (en orden):
  1. Header  `X-Tenant-ID`
  2. Subdominio del Host (tenant1.app.com → tenant1)
  3. Default: tenant "public"

En Fase 1 el catálogo es un CSV compartido (tenant "public"); a partir de la
Fase MT-2 todos los modelos (productos, órdenes, suscriptores, blog, campañas…)
llevarán `tenant_id` y se migrará a Postgres con Row-Level Security.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("vertex-tenancy")

DEFAULT_TENANT = os.getenv("DEFAULT_TENANT", "public")
ROOT_DOMAIN = os.getenv("ROOT_DOMAIN", "localhost")  # ej.: "vertexapp.com"


def resolve_tenant(host: Optional[str], header_tenant: Optional[str]) -> str:
    """Resuelve el tenant a partir del Host y/o header."""
    if header_tenant and header_tenant.strip():
        return header_tenant.strip().lower()
    if host:
        host = host.split(":")[0].lower()
        # subdominio directo: {tenant}.vertexapp.com
        if ROOT_DOMAIN != "localhost" and host.endswith("." + ROOT_DOMAIN):
            sub = host[: -len(ROOT_DOMAIN) - 1]
            if sub and sub not in ("www", "api", "admin"):
                return sub
        # localhost dev: {tenant}.localhost
        if host.endswith(".localhost"):
            sub = host[: -len(".localhost")]
            if sub:
                return sub
    return DEFAULT_TENANT


class TenantMiddleware(BaseHTTPMiddleware):
    """Inyecta `request.state.tenant` disponible en TODOS los endpoints."""

    async def dispatch(self, request: Request, call_next):
        tenant = resolve_tenant(
            request.headers.get("host"),
            request.headers.get("x-tenant-id"),
        )
        request.state.tenant = tenant
        logger.debug("tenant=%s path=%s", tenant, request.url.path)
        response = await call_next(request)
        response.headers["X-Tenant-ID"] = tenant  # trazabilidad
        return response
