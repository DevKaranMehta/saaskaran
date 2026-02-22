"""Tests for the enhanced Todo List extension."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta


# ---------------------------------------------------------------------------
# Extension metadata
# ---------------------------------------------------------------------------

def test_extension_metadata():
    from extensions.todo_list.extension import TodoListExtension
    ext = TodoListExtension()
    assert ext.name == "todo_list"
    assert ext.api_prefix == "/todo-list"
    assert "todo_list.read" in ext.permissions
    assert "todo_list.write" in ext.permissions


def test_default_config():
    from extensions.todo_list.extension import TodoListExtension
    config = TodoListExtension().default_config()
    assert config["default_priority"] == "medium"
    assert config["allow_recurring"] is True
    assert config["max_subtasks_per_todo"] == 50


# ---------------------------------------------------------------------------
# Model table names
# ---------------------------------------------------------------------------

def test_table_names_have_ext_prefix():
    from extensions.todo_list.models import (
        Todo,
        TodoActivityLog,
        TodoCategory,
        TodoComment,
        TodoSubtask,
    )
    assert Todo.__tablename__.startswith("ext_")
    assert TodoCategory.__tablename__.startswith("ext_")
    assert TodoSubtask.__tablename__.startswith("ext_")
    assert TodoComment.__tablename__.startswith("ext_")
    assert TodoActivityLog.__tablename__.startswith("ext_")


# ---------------------------------------------------------------------------
# Enum values
# ---------------------------------------------------------------------------

def test_priority_enum_values():
    from extensions.todo_list.models import PriorityEnum
    assert set(e.value for e in PriorityEnum) == {"low", "medium", "high"}


def test_recurrence_enum_values():
    from extensions.todo_list.models import RecurrenceEnum
    assert set(e.value for e in RecurrenceEnum) == {"none", "daily", "weekly", "monthly"}


def test_activity_action_enum_values():
    from extensions.todo_list.models import ActivityActionEnum
    expected = {
        "created", "updated", "completed", "reopened",
        "subtask_added", "subtask_completed", "comment_added", "category_changed",
    }
    assert set(e.value for e in ActivityActionEnum) == expected


# ---------------------------------------------------------------------------
# Helper: _recalculate_progress
# ---------------------------------------------------------------------------

def test_progress_no_subtasks_incomplete():
    from extensions.todo_list.routes import _recalculate_progress
    from extensions.todo_list.models import Todo
    todo = Todo.__new__(Todo)
    todo.subtasks = []
    todo.is_completed = False
    assert _recalculate_progress(todo) == 0.0


def test_progress_no_subtasks_completed():
    from extensions.todo_list.routes import _recalculate_progress
    from extensions.todo_list.models import Todo
    todo = Todo.__new__(Todo)
    todo.subtasks = []
    todo.is_completed = True
    assert _recalculate_progress(todo) == 100.0


def test_progress_partial_subtasks():
    from extensions.todo_list.routes import _recalculate_progress
    from extensions.todo_list.models import Todo, TodoSubtask
    todo = Todo.__new__(Todo)
    s1 = TodoSubtask.__new__(TodoSubtask)
    s1.is_completed = True
    s2 = TodoSubtask.__new__(TodoSubtask)
    s2.is_completed = False
    s3 = TodoSubtask.__new__(TodoSubtask)
    s3.is_completed = False
    todo.subtasks = [s1, s2, s3]
    todo.is_completed = False
    assert _recalculate_progress(todo) == round(1 / 3 * 100, 1)


def test_progress_all_subtasks_done():
    from extensions.todo_list.routes import _recalculate_progress
    from extensions.todo_list.models import Todo, TodoSubtask
    todo = Todo.__new__(Todo)
    subtasks = []
    for _ in range(4):
        s = TodoSubtask.__new__(TodoSubtask)
        s.is_completed = True
        subtasks.append(s)
    todo.subtasks = subtasks
    todo.is_completed = False
    assert _recalculate_progress(todo) == 100.0


# ---------------------------------------------------------------------------
# Helper: _next_occurrence
# ---------------------------------------------------------------------------

def test_next_occurrence_none():
    from extensions.todo_list.routes import _next_occurrence
    from extensions.todo_list.models import RecurrenceEnum
    now = datetime.now(UTC)
    assert _next_occurrence(RecurrenceEnum.none, now) is None


def test_next_occurrence_daily():
    from extensions.todo_list.routes import _next_occurrence
    from extensions.todo_list.models import RecurrenceEnum
    now = datetime.now(UTC)
    result = _next_occurrence(RecurrenceEnum.daily, now)
    assert result == now + timedelta(days=1)


def test_next_occurrence_weekly():
    from extensions.todo_list.routes import _next_occurrence
    from extensions.todo_list.models import RecurrenceEnum
    now = datetime.now(UTC)
    result = _next_occurrence(RecurrenceEnum.weekly, now)
    assert result == now + timedelta(weeks=1)


def test_next_occurrence_monthly():
    from extensions.todo_list.routes import _next_occurrence
    from extensions.todo_list.models import RecurrenceEnum
    now = datetime.now(UTC)
    result = _next_occurrence(RecurrenceEnum.monthly, now)
    assert result == now + timedelta(days=30)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_category_create_valid_color():
    from extensions.todo_list.schemas import CategoryCreate
    cat = CategoryCreate(name="Work", color="#ff5733")
    assert cat.color == "#ff5733"


def test_todo_create_defaults():
    from extensions.todo_list.schemas import TodoCreate
    from extensions.todo_list.models import PriorityEnum, RecurrenceEnum
    todo = TodoCreate(title="Buy milk")
    assert todo.priority == PriorityEnum.medium
    assert todo.recurrence == RecurrenceEnum.none
    assert todo.subtasks == []


def test_todo_create_with_subtasks():
    from extensions.todo_list.schemas import SubtaskCreate, TodoCreate
    todo = TodoCreate(
        title="Big task",
        subtasks=[SubtaskCreate(title="Step 1"), SubtaskCreate(title="Step 2")],
    )
    assert len(todo.subtasks) == 2
    assert todo.subtasks[0].title == "Step 1"
