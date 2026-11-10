from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.workorder import WorkOrder
from app.schemas.workorder import WorkOrderResponse, WorkOrderTransitionRequest
from app.state_machine.workorder import WorkOrderStateMachine

router = APIRouter(prefix="/api/workorders", tags=["工单管理"])


@router.get("", response_model=List[WorkOrderResponse], summary="查询维修工单列表")
def get_workorders(
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db)
):
    stmt = select(WorkOrder).order_by(WorkOrder.created_at.desc())
    if status:
        stmt = stmt.where(WorkOrder.status == status)
    orders = db.execute(stmt).scalars().all()
    return orders


@router.get("/{order_id}", response_model=WorkOrderResponse, summary="查询工单详情")
def get_workorder(order_id: int, db: Session = Depends(get_db)):
    order = db.get(WorkOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return order


@router.post("/{order_id}/transition", response_model=WorkOrderResponse, summary="触发工单状态机流转")
def transition_workorder(
    order_id: int,
    req: WorkOrderTransitionRequest,
    db: Session = Depends(get_db)
):
    order = db.get(WorkOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    updated_order = WorkOrderStateMachine.transition(
        session=db,
        workorder=order,
        target_state=req.target_state,
        operator=req.operator,
        solution_note=req.solution_note
    )
    return updated_order
