from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db_session
from app.models.user import User
from app.api.deps import get_current_admin_user
from app.repositories.user_repo import UserRepository

router = APIRouter()

@router.get("/pending")
async def get_pending_users(
    db: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin_user)
):
    user_repo = UserRepository(db)
    users = await user_repo.get_pending_users()
    
    return [
        {
            "id": str(u.id),
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "created_at": u.created_at
        } for u in users
    ]

@router.post("/{user_id}/approve")
async def approve_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin_user)
):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user_repo = UserRepository(db)
    user = await user_repo.get(user_uuid)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_approved = True
    await db.commit()
    
    return {"msg": f"User {user.email} approved successfully"}
