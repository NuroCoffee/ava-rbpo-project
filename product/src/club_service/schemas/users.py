from pydantic import BaseModel, ConfigDict, EmailStr

from club_service.domain.enums import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
