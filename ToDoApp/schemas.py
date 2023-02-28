from datetime import date
from pydantic import BaseModel
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
    email: str
    name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    tasks: List[Task] = []

    class Config:
        orm_mode = True

