from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select

from app.deps import CurrentUser, DbSession
from app.models import Priority, Task, TaskStatus
from app.schemas import TaskCreate, TaskOut, TaskPage, TaskStats, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

SORT_FIELDS = {
    "created_at": Task.created_at,
    "due_date": Task.due_date,
    "priority": Task.priority,
    "title": Task.title,
}


def get_owned_task(db: DbSession, user: CurrentUser, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@router.get("", response_model=TaskPage)
def list_tasks(
    db: DbSession,
    user: CurrentUser,
    status_: TaskStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    q: str | None = Query(default=None, description="Search in title and description"),
    sort: Literal["created_at", "due_date", "priority", "title"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TaskPage:
    query = select(Task).where(Task.owner_id == user.id)
    if status_ is not None:
        query = query.where(Task.status == status_)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(Task.title.ilike(pattern), Task.description.ilike(pattern)))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    column = SORT_FIELDS[sort]
    query = query.order_by(column.asc() if order == "asc" else column.desc(), Task.id)
    items = db.scalars(query.limit(limit).offset(offset)).all()
    return TaskPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/stats", response_model=TaskStats)
def task_stats(db: DbSession, user: CurrentUser) -> TaskStats:
    rows = db.execute(
        select(Task.status, func.count()).where(Task.owner_id == user.id).group_by(Task.status)
    ).all()
    by_status = {s: 0 for s in TaskStatus}
    by_status.update({s: n for s, n in rows})
    overdue = db.scalar(
        select(func.count()).where(
            Task.owner_id == user.id,
            Task.status != TaskStatus.done,
            Task.due_date < date.today(),
        )
    ) or 0
    return TaskStats(total=sum(by_status.values()), by_status=by_status, overdue=overdue)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: DbSession, user: CurrentUser) -> Task:
    task = Task(**data.model_dump(), owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: DbSession, user: CurrentUser) -> Task:
    return get_owned_task(db, user, task_id)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: DbSession, user: CurrentUser) -> Task:
    task = get_owned_task(db, user, task_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: DbSession, user: CurrentUser) -> Response:
    task = get_owned_task(db, user, task_id)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
