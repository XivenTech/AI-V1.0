from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactResponse, ContactUpdate

router = APIRouter(prefix="/api/contacts", tags=["应急联系人管理"])


@router.get("", response_model=List[ContactResponse], summary="查询所有值班联系人列表")
def get_contacts(db: Session = Depends(get_db)):
    stmt = select(Contact).order_by(Contact.priority.asc())
    contacts = db.execute(stmt).scalars().all()
    return contacts


@router.put("/{contact_id}", response_model=ContactResponse, summary="更新联系人真实手机号及配置")
def update_contact(
    contact_id: int,
    req: ContactUpdate,
    db: Session = Depends(get_db)
):
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    contact.name = req.name
    contact.phone = req.phone
    contact.role = req.role
    contact.is_active = req.is_active
    db.commit()
    db.refresh(contact)
    return contact
