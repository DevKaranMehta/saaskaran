"""Kanban Board Extension."""
from __future__ import annotations

from saas_builder.core import ExtensionBase


class KanbanBoardExtension(ExtensionBase):
    name = "kanban_board"
    version = "1.0.0"
    description = (
        "Trello-style Kanban board with drag-and-drop cards, "
        "multiple boards, priorities, due dates, and tags."
    )
    author = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix = "/kanban-board"
    permissions = ["kanban_board.read", "kanban_board.write"]
    admin_menu = [
        {
            "label": "Kanban Board",
            "icon": "layout",
            "route": "/admin/kanban-board",
        }
    ]

    def default_config(self) -> dict:
        return {
            "default_status": "todo",
            "allow_unassigned_cards": True,
        }

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
