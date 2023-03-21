from sqlalchemy.orm import Session
import app.models as models
import app.schemas as schemas
from datetime import datetime, date


def get_user_by_email(db: Session, user_email: str):
    """
    this func returns the user given email
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


def update_token(db: Session, token: schemas.TokenBase, token_id: int):
    """
    This function updates the token value (changed expiry time)
    :param db:
    :param token:
    :param token_id:
    :return:
    """
    db.query(models.Token).filter(models.Token.id == token_id).update(token.dict())
    db.commit()
    return token


def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    """
    this function creates new task for user in db
    :param db:
    :param task:
    :param user_id:
    :return:
    """
    db_task = models.Task(**task.dict(), owner_id=user_id, status=False)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task_by_title(db: Session, task_title: str, user_id: int):
    """
    this func returns a
    :param db:
    :param user_id:
    :param task_title:
    :return:
    """
    return db.query(models.Task).filter(models.Task.title == task_title, models.Task.owner_id == user_id).first()


def get_tasks_by_user(db: Session, user_id: int):
    """
    get all tasks by userid
    :param db:
    :param user_id:
    :return:
    """
    return db.query(models.Task).filter(models.Task.owner_id == user_id).all()


def get_single_task_by_user(db: Session, user_id: int, task_id: int):
    """
    this function returns a task by user
    :param db:
    :param user_id:
    :param task_id:
    :return:
    """
    return db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == user_id).first()


def update_task_by_user(db: Session, user_id: int, task_id: int, task: schemas.TaskCreate):
    """
    this function first queries if task exists and then updates the task
    :param db:
    :param user_id:
    :param task_id:
    :param task:
    :return:
    """
    if get_single_task_by_user(db, user_id, task_id):
        db.query(models.Task).filter(models.Task.id == task_id).update(task.dict())
        db.commit()
        return task
    return None


def delete_task(db: Session, user_id: int, task_id: int):
    """
    this function deletes user task
    :param db:
    :param user_id:
    :param task_id:
    :return:
    """
    if not get_single_task_by_user(db, user_id, task_id):
        return None
    res = db.query(models.Task).filter(models.Task.owner_id == user_id, models.Task.id == task_id).delete()
    db.commit()
    return res


def get_tasks_due_today(db: Session, user_id: int):
    """
    return list of all tasks due today
    :param db:
    :param user_id:
    :return:
    """
    return db.query(models.Task).filter(models.Task.owner_id == user_id, models.Task.due_date == date.today(),
                                        models.Task.status == False).all()


def get_complete_tasks_by_user(db: Session, user_id: int):
    """
    returns list of completed tasks
    :param db:
    :param user_id:
    :return:
    """
    return db.query(models.Task).filter(models.Task.owner_id == user_id, models.Task.status == True).all()


def complete_task(db: Session, user_id: int, task_id: int):
    """
    updates status of a task
    :param db:
    :param user_id:
    :param task_id:
    :return:
    """
    if get_single_task_by_user(db, user_id, task_id):
        db.query(models.Task).filter(models.Task.id == task_id).update({models.Task.status: True})
        db.commit()
        return {"Message": "successfully finished task"}
    return {}


def get_all_users(db: Session):
    """
    this func returns the user given email
    :param db:
    :param user_email:
    :return:
    """
    return db.query(models.User).all()
