from datetime import date
from pydantic import BaseModel, EmailStr
from typing import List, Union


# Tasks Schema
class TaskBase(BaseModel):
    title: str
    description: Union[str, None] = None
    due_date: date


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: int
    owner_id: int
    status: bool = False

    class Config:
        orm_mode = True


# User Schema
class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    tasks: List[Task] = []

    registered_on: date
    registration_confirm: bool = False

    class Config:
        orm_mode = True


# token schema
class TokenBase(BaseModel):
    access_token: str
    token_type: str


class TokenCreateAndReturn(TokenBase):
    user_id: int

    class Config:
        orm_mode = True


# user login schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str
