from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    name: str
    role: str
    phone: str
    priority: int = 1
    is_active: bool = True


class ContactUpdate(BaseModel):
    name: str
    phone: str
    role: str
    is_active: bool = True


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str
    phone: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
