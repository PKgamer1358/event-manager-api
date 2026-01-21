from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ============================================
# USER SCHEMAS
# ============================================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=120)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=120)
    last_name: Optional[str] = Field(None, max_length=120)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    is_admin: bool = False


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    roll_number: Optional[str] = None
    branch: Optional[str] = None
    year_of_study: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserInToken(BaseModel):
    id: int
    username: str
    is_admin: bool


# ============================================
# TOKEN SCHEMAS
# ============================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInToken


class TokenData(BaseModel):
    user_id: Optional[int] = None
    is_admin: bool = False

class TokenRequest(BaseModel):
    token: str
# ============================================
# STUDENT SCHEMAS
# ============================================

class StudentSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=120)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=120)
    last_name: Optional[str] = Field(None, max_length=120)
    password: str = Field(..., min_length=6)
    #college_id: int
    roll_number: Optional[str] = Field(None, max_length=50)
    branch: Optional[str] = Field(None, max_length=100)
    year_of_study: Optional[int] = Field(None, ge=1, le=4)


# ============================================
# COLLEGE SCHEMAS
# ============================================

# class CollegeBase(BaseModel):
#     name: str = Field(..., min_length=1, max_length=255)
#     code: str = Field(..., min_length=1, max_length=50)
#     city: Optional[str] = Field(None, max_length=100)
#     contact_email: Optional[EmailStr] = None
#     contact_phone: Optional[str] = Field(None, max_length=20)
#     website: Optional[str] = Field(None, max_length=255)
#     is_active: bool = True


# class CollegeCreate(CollegeBase):
#     pass


# class CollegeResponse(CollegeBase):
#     id: int
#     created_at: datetime
#     updated_at: datetime
    
#     model_config = ConfigDict(from_attributes=True)


# ============================================
# EVENT SCHEMAS
# ============================================

class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=1)   # ✅ ADD
    club: Optional[str] = None 
    venue: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    capacity: Optional[int] = Field(None, ge=1)
    image_url: Optional[str] = None

class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None   # ✅ ADD
    club: Optional[str] = None       # ✅ ADD

    venue: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = Field(None, ge=1)


class EventResponse(EventBase):
    id: int
    created_by: int
    created_at: datetime
    registered_count: int
    is_full: bool
    image_url: Optional[str]
    image_url: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class EventMediaResponse(BaseModel):
    id: int
    event_id: int
    file_url: str
    file_type: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)



# ============================================
# REGISTRATION SCHEMAS
# ============================================

class RegistrationBase(BaseModel):
    event_id: int


class RegistrationCreate(RegistrationBase):
    pass


class RegistrationResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    registered_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RegistrationWithUser(RegistrationResponse):
    user: UserResponse
    
    model_config = ConfigDict(from_attributes=True)


class RegistrationWithEvent(RegistrationResponse):
    event: EventResponse
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# RESPONSE MESSAGES
# ============================================

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

class StudentAdminResponse(BaseModel):
    year_of_study: int | None
    branch: str | None

    class Config:
        orm_mode = True

class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: str | None
    is_active: bool
    is_admin: bool
    student: StudentAdminResponse | None

    class Config:
        orm_mode = True
