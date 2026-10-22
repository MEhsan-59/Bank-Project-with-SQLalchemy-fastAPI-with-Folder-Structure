from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=30)
    user_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


class AccountLogin(BaseModel):
    user_id: str
    password: str


class AccountCreated(BaseModel):
    status: bool
    message: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=72)
    new_password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str = Field(..., min_length=8, max_length=72)


class ChangePasswordResponse(BaseModel):
    success: bool
    message: str
