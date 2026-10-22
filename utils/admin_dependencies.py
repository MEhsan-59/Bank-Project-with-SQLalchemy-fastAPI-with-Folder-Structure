from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from utils.dependencies import bearer_scheme
from utils.security import decode_access_token


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    payload = decode_access_token(credentials.credentials)
    if payload is None or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return payload


def require_admin_permission(permission: str):
    def check_permission(
        admin: dict = Depends(get_current_admin),
    ) -> dict:
        permissions = admin.get("permissions", [])
        if not isinstance(permissions, list) or permission not in permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Admin permission required: {permission}.",
            )
        return admin

    return check_permission
