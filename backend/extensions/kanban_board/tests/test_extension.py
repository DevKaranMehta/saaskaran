"""Tests for the Kanban Board extension."""
from __future__ import annotations


def test_extension_metadata():
    from extensions.kanban_board.extension import KanbanBoardExtension
    ext = KanbanBoardExtension()
    assert ext.name == "kanban_board"
    assert ext.api_prefix == "/kanban-board"
    assert "kanban_board.read" in ext.permissions
    assert "kanban_board.write" in ext.permissions


def test_default_config():
    from extensions.kanban_board.extension import KanbanBoardExtension
    config = KanbanBoardExtension().default_config()
    assert config["default_status"] == "todo"


def test_table_names_have_ext_prefix():
    from extensions.kanban_board.models import KanbanBoard, KanbanCard
    assert KanbanBoard.__tablename__.startswith("ext_")
    assert KanbanCard.__tablename__.startswith("ext_")


def test_card_status_enum_values():
    from extensions.kanban_board.models import CardStatus
    expected = {"backlog", "todo", "in_progress", "review", "done"}
    assert set(e.value for e in CardStatus) == expected


def test_priority_enum_values():
    from extensions.kanban_board.models import Priority
    assert set(e.value for e in Priority) == {"low", "medium", "high"}


def test_board_response_schema():
    from extensions.kanban_board.schemas import BoardCreate
    b = BoardCreate(name="My Board", description="Test")
    assert b.name == "My Board"


def test_card_create_defaults():
    from extensions.kanban_board.schemas import CardCreate
    from extensions.kanban_board.models import CardStatus, Priority
    c = CardCreate(title="Test Card")
    assert c.status == CardStatus.todo
    assert c.priority == Priority.medium
    assert c.tags == []
