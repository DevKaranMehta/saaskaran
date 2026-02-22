"""Todo List Extension — FastAPI routes."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import User

from .models import (
    ActivityActionEnum,
    PriorityEnum,
    RecurrenceEnum,
    Todo,
    TodoActivityLog,
    TodoCategory,
    TodoComment,
    TodoSubtask,
)
from .schemas import (
    ActivityLogResponse,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    SubtaskCreate,
    SubtaskResponse,
    SubtaskUpdate,
    TodoCreate,
    TodoResponse,
    TodoUpdate,
)

router = APIRouter(tags=["todo-list"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recalculate_progress(todo: Todo) -> float:
    """Return progress percentage based on completed subtasks."""
    if not todo.subtasks:
        return 100.0 if todo.is_completed else 0.0
    completed = sum(1 for s in todo.subtasks if s.is_completed)
    return round((completed / len(todo.subtasks)) * 100, 1)


def _next_occurrence(recurrence: RecurrenceEnum, from_dt: datetime) -> datetime | None:
    """Calculate the next recurrence datetime."""
    if recurrence == RecurrenceEnum.daily:
        return from_dt + timedelta(days=1)
    if recurrence == RecurrenceEnum.weekly:
        return from_dt + timedelta(weeks=1)
    if recurrence == RecurrenceEnum.monthly:
        return from_dt + timedelta(days=30)
    return None


async def _log(
    db: AsyncSession,
    tenant_id: str,
    todo_id: str,
    actor_id: str,
    action: ActivityActionEnum,
    detail: str | None = None,
) -> None:
    entry = TodoActivityLog(
        tenant_id=tenant_id,
        todo_id=todo_id,
        actor_id=actor_id,
        action=action,
        detail=detail,
    )
    db.add(entry)


async def _get_todo_or_404(db: AsyncSession, todo_id: str, tenant_id: str) -> Todo:
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.tenant_id == tenant_id)
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


# ===========================================================================
# CATEGORIES
# ===========================================================================

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TodoCategory)
        .where(TodoCategory.tenant_id == current_user.tenant_id)
        .order_by(TodoCategory.name)
    )
    return result.scalars().all()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = TodoCategory(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=payload.name,
        color=payload.color,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TodoCategory).where(
            TodoCategory.id == category_id,
            TodoCategory.tenant_id == current_user.tenant_id,
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TodoCategory).where(
            TodoCategory.id == category_id,
            TodoCategory.tenant_id == current_user.tenant_id,
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)
    await db.commit()


# ===========================================================================
# TODOS
# ===========================================================================

@router.get("/todos", response_model=list[TodoResponse])
async def list_todos(
    is_completed: Optional[bool] = Query(None),
    priority: Optional[PriorityEnum] = Query(None),
    category_id: Optional[str] = Query(None),
    recurrence: Optional[RecurrenceEnum] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Todo).where(Todo.tenant_id == current_user.tenant_id)
    if is_completed is not None:
        stmt = stmt.where(Todo.is_completed == is_completed)
    if priority:
        stmt = stmt.where(Todo.priority == priority)
    if category_id:
        stmt = stmt.where(Todo.category_id == category_id)
    if recurrence:
        stmt = stmt.where(Todo.recurrence == recurrence)
    stmt = stmt.order_by(Todo.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.category_id:
        cat_result = await db.execute(
            select(TodoCategory).where(
                TodoCategory.id == payload.category_id,
                TodoCategory.tenant_id == current_user.tenant_id,
            )
        )
        if not cat_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Category not found")

    todo = Todo(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        recurrence=payload.recurrence,
        category_id=payload.category_id,
        next_occurrence=_next_occurrence(
            payload.recurrence, payload.due_date or datetime.now(UTC)
        ),
    )
    db.add(todo)
    await db.flush()

    for idx, st in enumerate(payload.subtasks):
        db.add(TodoSubtask(
            tenant_id=current_user.tenant_id,
            todo_id=todo.id,
            title=st.title,
            order=st.order if st.order else idx,
        ))

    await db.flush()
    todo.progress = _recalculate_progress(todo)

    await _log(db, current_user.tenant_id, todo.id, current_user.id, ActivityActionEnum.created)
    await db.commit()
    await db.refresh(todo)
    return todo


@router.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_todo_or_404(db, todo_id, current_user.tenant_id)


@router.patch("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: str,
    payload: TodoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = await _get_todo_or_404(db, todo_id, current_user.tenant_id)

    if payload.category_id is not None:
        cat_result = await db.execute(
            select(TodoCategory).where(
                TodoCategory.id == payload.category_id,
                TodoCategory.tenant_id == current_user.tenant_id,
            )
        )
        if not cat_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Category not found")
        old_cat = todo.category_id
        if old_cat != payload.category_id:
            await _log(
                db, current_user.tenant_id, todo.id, current_user.id,
                ActivityActionEnum.category_changed,
                detail=f"category changed from {old_cat} to {payload.category_id}",
            )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    if "recurrence" in update_data or "due_date" in update_data:
        todo.next_occurrence = _next_occurrence(
            todo.recurrence, todo.due_date or datetime.now(UTC)
        )

    await _log(db, current_user.tenant_id, todo.id, current_user.id, ActivityActionEnum.updated)
    await db.commit()
    await db.refresh(todo)
    return todo


@router.post("/todos/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(
    todo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle a todo as completed. Recurring todos auto-regenerate."""
    todo = await _get_todo_or_404(db, todo_id, current_user.tenant_id)

    if todo.is_completed:
        # Re-open
        todo.is_completed = False
        todo.completed_at = None
        todo.progress = _recalculate_progress(todo)
        await _log(
            db, current_user.tenant_id, todo.id, current_user.id, ActivityActionEnum.reopened
        )
    else:
        todo.is_completed = True
        todo.completed_at = datetime.now(UTC)
        todo.progress = 100.0
        await _log(
            db, current_user.tenant_id, todo.id, current_user.id, ActivityActionEnum.completed
        )

        # Auto-generate next occurrence for recurring todos
        if todo.recurrence != RecurrenceEnum.none and todo.next_occurrence:
            new_todo = Todo(
                tenant_id=todo.tenant_id,
                created_by=todo.created_by,
                title=todo.title,
                description=todo.description,
                priority=todo.priority,
                due_date=todo.next_occurrence,
                recurrence=todo.recurrence,
                category_id=todo.category_id,
                next_occurrence=_next_occurrence(todo.recurrence, todo.next_occurrence),
            )
            db.add(new_todo)
            await db.flush()
            await _log(
                db, current_user.tenant_id, new_todo.id, current_user.id,
                ActivityActionEnum.created,
                detail=f"auto-generated from recurring todo {todo.id}",
            )

    await db.commit()
    await db.refresh(todo)
    return todo


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    await db.delete(todo)
    await db.commit()


# ===========================================================================
# SUBTASKS
# ===========================================================================

@router.post(
    "/todos/{todo_id}/subtasks",
    response_model=SubtaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_subtask(
    todo_id: str,
    payload: SubtaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    subtask = TodoSubtask(
        tenant_id=current_user.tenant_id,
        todo_id=todo.id,
        title=payload.title,
        order=payload.order,
    )
    db.add(subtask)
    await db.flush()
    await db.refresh(todo)
    todo.progress = _recalculate_progress(todo)
    await _log(
        db, current_user.tenant_id, todo.id, current_user.id,
        ActivityActionEnum.subtask_added,
        detail=f"subtask added: {payload.title}",
    )
    await db.commit()
    await db.refresh(subtask)
    return subtask


@router.patch("/todos/{todo_id}/subtasks/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    todo_id: str,
    subtask_id: str,
    payload: SubtaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    result = await db.execute(
        select(TodoSubtask).where(
            TodoSubtask.id == subtask_id,
            TodoSubtask.todo_id == todo.id,
            TodoSubtask.tenant_id == current_user.tenant_id,
        )
    )
    subtask = result.scalar_one_or_none()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    was_completed = subtask.is_completed
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subtask, field, value)

    await db.flush()
    await db.refresh(todo)
    todo.progress = _recalculate_progress(todo)

    if not was_completed and subtask.is_completed:
        await _log(
            db, current_user.tenant_id, todo.id, current_user.id,
            ActivityActionEnum.subtask_completed,
            detail=f"subtask completed: {subtask.title}",
        )

    await db.commit()
    await db.refresh(subtask)
    return subtask


@router.delete(
    "/todos/{todo_id}/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subtask(
    todo_id: str,
    subtask_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    result = await db.execute(
        select(TodoSubtask).where(
            TodoSubtask.id == subtask_id,
            TodoSubtask.todo_id == todo.id,
            TodoSubtask.tenant_id == current_user.tenant_id,
        )
    )
    subtask = result.scalar_one_or_none()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    await db.delete(subtask)
    await db.flush()
    await db.refresh(todo)
    todo.progress = _recalculate_progress(todo)
    await db.commit()


# ===========================================================================
# COMMENTS
# ===========================================================================

@router.get("/todos/{todo_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    todo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    result = await db.execute(
        select(TodoComment)
        .where(
            TodoComment.todo_id == todo_id,
            TodoComment.tenant_id == current_user.tenant_id,
        )
        .order_by(TodoComment.created_at)
    )
    return result.scalars().all()


@router.post(
    "/todos/{todo_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    todo_id: str,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    comment = TodoComment(
        tenant_id=current_user.tenant_id,
        todo_id=todo.id,
        body=payload.body,
        created_by=current_user.id,
    )
    db.add(comment)
    await _log(
        db, current_user.tenant_id, todo.id, current_user.id,
        ActivityActionEnum.comment_added,
        detail="comment added",
    )
    await db.commit()
    await db.refresh(comment)
    return comment


@router.patch("/todos/{todo_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    todo_id: str,
    comment_id: str,
    payload: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    result = await db.execute(
        select(TodoComment).where(
            TodoComment.id == comment_id,
            TodoComment.todo_id == todo_id,
            TodoComment.tenant_id == current_user.tenant_id,
            TodoComment.created_by == current_user.id,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or not editable")
    comment.body = payload.body
    await db.commit()
    await db.refresh(comment)
    return comment


@router.delete(
    "/todos/{todo_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    todo_id: str,
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    result = await db.execute(
        select(TodoComment).where(
            TodoComment.id == comment_id,
            TodoComment.todo_id == todo_id,
            TodoComment.tenant_id == current_user.tenant_id,
            TodoComment.created_by == current_user.id,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or not deletable")
    await db.delete(comment)
    await db.commit()


# ===========================================================================
# ACTIVITY LOG
# ===========================================================================

@router.get("/todos/{todo_id}/activity", response_model=list[ActivityLogResponse])
async def get_activity(
    todo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_todo_or_404(db, todo_id, current_user.tenant_id)
    result = await db.execute(
        select(TodoActivityLog)
        .where(
            TodoActivityLog.todo_id == todo_id,
            TodoActivityLog.tenant_id == current_user.tenant_id,
        )
        .order_by(TodoActivityLog.created_at)
    )
    return result.scalars().all()
