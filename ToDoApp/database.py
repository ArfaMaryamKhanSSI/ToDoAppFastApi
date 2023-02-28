from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:abc123@localhost/todo"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
