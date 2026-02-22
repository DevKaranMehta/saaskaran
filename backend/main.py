"""SaaS Factory — FastAPI backend entry point."""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add backend dir to path so extensions can be discovered
sys.path.insert(0, str(Path(__file__).parent))

from api.database import create_tables
from api.routes.auth import router as auth_router
from api.routes.extensions import router as ext_router
from saas_builder.core import ExtensionManager, ExtensionRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── Templates shipped with platform ─────────────────────────────
# Extensions listed here must correspond to folders in /backend/extensions/
TEMPLATES: dict[str, dict] = {
    "blank":     {"name": "Blank",       "emoji": "✨", "extensions": ["admin", "settings", "roles"]},
    "lms":       {"name": "LMS",         "emoji": "📚", "extensions": ["admin", "settings", "roles", "billing", "blog_cms", "notifications", "audit_log"]},
    "crm":       {"name": "CRM",         "emoji": "📊", "extensions": ["admin", "settings", "roles", "billing", "invoicing", "kanban_board", "notifications", "audit_log"]},
    "helpdesk":  {"name": "Helpdesk",    "emoji": "🎧", "extensions": ["admin", "settings", "roles", "live_chat", "form_builder", "notifications", "customer_portal", "audit_log"]},
    "ecommerce": {"name": "E-commerce",  "emoji": "🛒", "extensions": ["admin", "settings", "roles", "billing", "invoicing", "notifications", "customer_portal", "audit_log"]},
    "hr":        {"name": "HR System",   "emoji": "👥", "extensions": ["admin", "settings", "roles", "form_builder", "notifications", "audit_log"]},
    "saas":      {"name": "SaaS Starter","emoji": "🚀", "extensions": ["admin", "settings", "roles", "billing", "marketplace", "notifications", "customer_portal", "audit_log"]},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────
    logger.info("Starting SaaS Factory backend...")

    # Discover extensions
    registry = ExtensionRegistry()
    registry.discover(Path(__file__).parent / "extensions")
    app.state.ext_registry = registry

    # Mount routes FIRST — this imports extension routes/models into Base.metadata
    manager = ExtensionManager(app, registry)
    manager.mount_all()
    app.state.ext_manager = manager

    # Create DB tables AFTER all extension models are imported
    await create_tables()

    # Store templates config
    app.state.templates = TEMPLATES

    logger.info("SaaS Factory backend ready — %d extensions loaded", len(registry.all()))
    yield

    # ── Shutdown ─────────────────────────────────────────────────
    logger.info("Shutting down SaaS Factory backend...")


app = FastAPI(
    title="SaaS Factory API",
    version="1.0.0",
    description="Backend API for SaaS Factory platform",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend + any website that embeds the chat widget
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Platform routes
app.include_router(auth_router)
app.include_router(ext_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "saas-factory-backend"}


@app.get("/api/v1/templates")
async def list_templates():
    return {"templates": TEMPLATES}
