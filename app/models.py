from sqlalchemy.orm import relationship
from app.database import Base, engine
from sqlalchemy import String, Boolean, Integer, Column, ForeignKey, Date


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    password = Column(String)

    registered_on = Column(Date)
    registration_confirm = Column(Boolean, default=False)

    tasks = relationship("Task", back_populates="owner")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    due_date = Column(Date)
    status = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="tasks")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(String)
    token_type = Column(String)


Base.metadata.create_all(bind=engine)
