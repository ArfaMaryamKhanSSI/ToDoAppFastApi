import os

from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine(os.environ.get("SQLALCHEMY_DATABASE_URL"))

LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
Base.metadata.create_all(bind=engine)


def get_DB():
    db = LocalSession()
    try:
        yield db
    finally:
        db.close()
