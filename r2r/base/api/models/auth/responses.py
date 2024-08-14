from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class ResultsWrapper(BaseModel, Generic[T]):
    results: T


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    is_verified: bool = False
    group_ids: list[UUID] = []

    # Optional fields (to update or set at creation)
    hashed_password: Optional[str] = None
    verification_code_expiry: Optional[datetime] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None


class GenericMessageResponse(BaseModel):
    message: str


# Create wrapped versions of each response
WrappedTokenResponse = ResultsWrapper[TokenResponse]
WrappedUserResponse = ResultsWrapper[UserResponse]
WrappedGenericMessageResponse = ResultsWrapper[GenericMessageResponse]
