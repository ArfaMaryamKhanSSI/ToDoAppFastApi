from sqlalchemy.orm import Session
import models
import schemas
from datetime import datetime


def get_user_by_email(db: Session, user_email: str):
    """
    this func returns the user with given email
    :param db:
    :param user_email:
    :return:
    """
    return db.query(models.User).filter(models.User.email == user_email).first()


def create_user(db: Session, user: schemas.UserCreate):
    """
    this func creates the user in db
    :param db:
    :param user:
    :return:
    """
    db_user = models.User(email=user.email, password=user.password, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def confirmation(db: Session, email: str):
    """
    this func updates user confirmation status and time in db
    :param db:
    :param email:
    :return:
    """
    user = get_user_by_email(db, email)
    res = db.query(models.User).filter(models.User.email == email).update({models.User.registration_confirm: True,
                                                                           models.User.registered_on:
                                                                               datetime.utcnow()})
    db.commit()
    db.refresh(user)
    return res


def confirmed_user(db: Session, email: str):
    """
    this func returns if user is already confirmed
    :param db:
    :param email:
    :return:
    """
    return db.query(models.User).filter(models.User.email == email, models.User.registration_confirm == True).first()


def create_token(db: Session, token: schemas.TokenBase, user_id: int):
    """
    this func creates a token against user id in db
    :param db:
    :param token:
    :param user_id:
    :return:
    """
    db_token = models.Token(**token.dict(), user_id=user_id)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_token(db: Session, user_id: int):
    """
    this func returns the token against user id
    :param db:
    :param user_id:
    :return:
    """
    return db.query(models.Token).filter(models.Token.user_id == user_id).first()
