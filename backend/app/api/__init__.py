from fastapi import APIRouter
from app.api.devices import router as devices_router
from app.api.alarms import router as alarms_router
from app.api.calls import router as calls_router
from app.api.contacts import router as contacts_router
from app.api.workorders import router as workorders_router
from app.api.demo import router as demo_router

api_router = APIRouter()
api_router.include_router(devices_router)
api_router.include_router(alarms_router)
api_router.include_router(calls_router)
api_router.include_router(contacts_router)
api_router.include_router(workorders_router)
api_router.include_router(demo_router)

__all__ = ["api_router"]
