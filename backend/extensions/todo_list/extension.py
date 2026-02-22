"""Todo List Extension — Enhanced with subtasks, comments, recurrence, categories, and activity log."""
from __future__ import annotations

from saas_builder.core import ExtensionBase


class TodoListExtension(ExtensionBase):
    name = "todo_list"
    version = "1.0.0"
    description = (
        "Feature-rich todo list with subtasks, comments, recurring todos, "
        "categories, progress tracking, and full activity audit log."
    )
    author = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix = "/todo-list"
    permissions = ["todo_list.read", "todo_list.write", "todo_list.admin"]
    admin_menu = [
        {
            "label": "Todo List",
            "icon": "check-circle",
            "route": "/admin/todo-list",
        }
    ]

    def default_config(self) -> dict:
        return {
            "default_priority": "medium",
            "allow_recurring": True,
            "max_subtasks_per_todo": 50,
            "max_comments_per_todo": 200,
        }

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
