"""Kanban Board — FastAPI routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import User

from .models import KanbanBoard, KanbanCard
from .schemas import (
    BoardCreate, BoardResponse, BoardUpdate,
    CardCreate, CardResponse, CardUpdate,
)

router = APIRouter(tags=["kanban-board"])


# ── Board routes ──────────────────────────────────────────────────────────────

@router.get("/boards", response_model=list[BoardResponse])
async def list_boards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KanbanBoard)
        .where(KanbanBoard.tenant_id == current_user.tenant_id)
        .order_by(KanbanBoard.created_at.asc())
    )
    return result.scalars().all()


@router.post("/boards", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    payload: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = KanbanBoard(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


@router.get("/boards/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KanbanBoard).where(
            KanbanBoard.id == board_id,
            KanbanBoard.tenant_id == current_user.tenant_id,
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.patch("/boards/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: str,
    payload: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KanbanBoard).where(
            KanbanBoard.id == board_id,
            KanbanBoard.tenant_id == current_user.tenant_id,
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(board, field, value)
    await db.commit()
    await db.refresh(board)
    return board


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KanbanBoard).where(
            KanbanBoard.id == board_id,
            KanbanBoard.tenant_id == current_user.tenant_id,
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    await db.delete(board)
    await db.commit()
    return None


# ── Card routes ───────────────────────────────────────────────────────────────

@router.get("/boards/{board_id}/cards", response_model=list[CardResponse])
async def list_cards(
    board_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify board ownership
    board_result = await db.execute(
        select(KanbanBoard).where(
            KanbanBoard.id == board_id,
            KanbanBoard.tenant_id == current_user.tenant_id,
        )
    )
    if not board_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Board not found")

    result = await db.execute(
        select(KanbanCard)
        .where(
            KanbanCard.board_id == board_id,
            KanbanCard.tenant_id == current_user.tenant_id,
        )
        .order_by(KanbanCard.position.asc(), KanbanCard.created_at.asc())
    )
    return result.scalars().all()


@router.post("/boards/{board_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    board_id: str,
    payload: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board_result = await db.execute(
        select(KanbanBoard).where(
            KanbanBoard.id == board_id,
            KanbanBoard.tenant_id == current_user.tenant_id,
        )
    )
    if not board_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Board not found")

    card = KanbanCard(
        board_id=board_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        position=payload.position,
        tags=payload.tags,
        assigned_to=payload.assigned_to,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


@router.patch("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: str,
    payload: CardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KanbanCard).where(
            KanbanCard.id == card_id,
            KanbanCard.tenant_id == current_user.tenant_id,
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    await db.commit()
    await db.refresh(card)
    return card


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KanbanCard).where(
            KanbanCard.id == card_id,
            KanbanCard.tenant_id == current_user.tenant_id,
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    await db.delete(card)
    await db.commit()
    return None
