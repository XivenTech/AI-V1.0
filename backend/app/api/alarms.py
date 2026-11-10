from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.database.session import get_db
from app.models.alarm import Alarm
from app.models.alarm_event import AlarmEvent
from app.schemas.alarm import AlarmResponse, AlarmEventResponse, AlarmTransitionRequest
from app.state_machine.alarm import AlarmStateMachine, InvalidStateTransitionException

router = APIRouter(prefix="/api/alarms", tags=["报警中心"])


@router.get("", response_model=List[AlarmResponse], summary="查询报警列表")
def get_alarms(
    status: Optional[str] = Query(None, description="状态过滤"),
    level: Optional[str] = Query(None, description="等级过滤"),
    db: Session = Depends(get_db)
):
    stmt = select(Alarm).options(
        selectinload(Alarm.device),
        selectinload(Alarm.ai_analysis)
    ).order_by(Alarm.created_at.desc())

    if status:
        stmt = stmt.where(Alarm.status == status)
    if level:
        stmt = stmt.where(Alarm.level == level)

    alarms = db.execute(stmt).scalars().all()
    return alarms


@router.get("/{alarm_id}", response_model=AlarmResponse, summary="查询报警详情")
def get_alarm(alarm_id: int, db: Session = Depends(get_db)):
    stmt = select(Alarm).options(
        selectinload(Alarm.device),
        selectinload(Alarm.ai_analysis)
    ).where(Alarm.id == alarm_id)
    alarm = db.execute(stmt).scalars().first()
    if not alarm:
        raise HTTPException(status_code=404, detail="报警记录不存在")
    return alarm


@router.get("/{alarm_id}/events", response_model=List[AlarmEventResponse], summary="查询报警状态机事件流水")
def get_alarm_events(alarm_id: int, db: Session = Depends(get_db)):
    stmt = select(AlarmEvent).where(AlarmEvent.alarm_id == alarm_id).order_by(AlarmEvent.created_at.desc())
    events = db.execute(stmt).scalars().all()
    return events


@router.post("/{alarm_id}/transition", response_model=AlarmResponse, summary="触发报警状态机流转")
def transition_alarm(
    alarm_id: int,
    req: AlarmTransitionRequest,
    db: Session = Depends(get_db)
):
    alarm = db.get(Alarm, alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="报警记录不存在")

    try:
        updated_alarm = AlarmStateMachine.transition(
            session=db,
            alarm=alarm,
            target_state=req.target_state,
            operator=req.operator,
            note=req.note
        )
        return updated_alarm
    except InvalidStateTransitionException as e:
        raise HTTPException(status_code=400, detail=str(e))
