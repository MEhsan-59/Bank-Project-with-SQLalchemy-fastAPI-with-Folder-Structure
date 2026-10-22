from pydantic import BaseModel


class AdminFreezeResponse(BaseModel):
    success: bool
    message: str
