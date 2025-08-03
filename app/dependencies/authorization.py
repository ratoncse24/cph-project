from fastapi import Depends, HTTPException, status
from typing import List
from app.dependencies.auth import get_current_user
from app.schemas.user import UserRead
from app.core.roles import UserRole


def require_roles(required_roles: List[UserRole]):
    def role_checker(user: UserRead = Depends(get_current_user)):
        if user.role_name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return user

    return role_checker
