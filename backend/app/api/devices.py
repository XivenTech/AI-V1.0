from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.device import Device
from app.schemas.device import DeviceResponse

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


@router.get("", response_model=List[DeviceResponse], summary="获取所有接入设备列表")
def get_devices(db: Session = Depends(get_db)):
    stmt = select(Device).order_by(Device.id.asc())
    devices = db.execute(stmt).scalars().all()
    return devices


@router.get("/{device_id}", response_model=DeviceResponse, summary="获取指定设备详情")
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device
