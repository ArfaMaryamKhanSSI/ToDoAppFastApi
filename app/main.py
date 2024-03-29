from typing import Union, List
from fastapi import Depends, FastAPI, HTTPException, Body, Request, Security, Header
from sqlalchemy.orm import Session
from starlette import status
from fastapi.responses import RedirectResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security
import app.task as task
import app.crud as crud
import app.utils as utils
import app.schemas as schemas
from app.database import get_DB
from app.task import celery

api_key = APIKeyHeader(name='Authorization')

app = FastAPI()

app.celery = celery


@app.get("/")
async def root():
    return RedirectResponse(url='/docs')


@app.post("/register/", tags=["todo/signup"], response_model=dict)
async def register(user: schemas.UserCreate = Body(default=None), db: Session = Depends(get_DB)):
    """
    This function adds the user in DB and sends a verification email
    :param user:
    :param db:
    :return:
    """
    db_user = crud.get_user_by_email(db, user_email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = utils.hash_password(user.password)
    user_db = schemas.UserCreate(email=user.email, name=user.name, password=hashed_password)
    stored_user = crud.create_user(db=db, user=user_db)
    verification_link = utils.create_token_link(db_user=stored_user, db=db)
    message = f"""
        Please click this link to verify your account.
        {verification_link}
        """
    subject = "Verify your account"
    r = task.send_email.delay(message=message, subject=subject, email=stored_user.email)
    return {"message": "please confirm your account on this link", "link": verification_link, "task_id": r.id}


@app.get('/simple_task_status/<task_id>')
def get_status(task_id):
    stat = task.app.AsyncResult(task_id, app=task.app)
    print("Invoking Method ")
    return "Status of the Task " + str(stat.state)


@app.get("/confirmation/{token}", tags=["todo/signup-confirmation"])
def confirmation(token: str, db: Session = Depends(get_DB)):
    """
    this function confirms the user by
    :param token:
    :param db:
    :return:
    """
    token = token.encode("utf-8")
    decrypt_token = utils.decrypt_token(token)
    decoded_token = utils.decode_token(decrypt_token)
    if not decoded_token:
        raise HTTPException(status_code=400, detail="Token expired")
    user = crud.get_user_by_email(db, decoded_token.get("email"))
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    res = crud.confirmed_user(db, user.email)
    if res:
        raise HTTPException(status_code=400, detail="User already registered")
    crud.confirmation(db, user.email)
    return {"Message": "User Confirmed"}


@app.post("/login/", response_model=Union[schemas.TokenBase, dict], tags=["todo/signin"])
async def login(req: Request, user: schemas.UserLogin = None, db: Session = Depends(get_DB)):
    """
    this func returns token if user is confirmed else it returns confirmation link
    :param req:
    :param user:
    :param db:
    :return:
    """
    data = await req.json()
    db_user = crud.get_user_by_email(db, user_email=data['email'])
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist"
        )

    is_user = utils.authenticate_user(data['email'], data['password'], db_user)
    if not is_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    res = crud.confirmed_user(db, db_user.email)
    if res:
        return utils.get_and_store_token(db_user=db_user, db=db)

    else:
        verification_link = utils.create_token_link(db_user=db_user, db=db)
        message = f"""
            Please click this link to verify your account.
            {verification_link}
            """
        subject = "Verify your account"
        r = task.send_email.delay(message=message, subject=subject, email=db_user.email)
        return {"message": "please confirm your account on this link", "link": verification_link, "task_id": r.id}


@app.post("/user/task/", response_model=dict, tags=["todo/create-task"])
def create_task(task: schemas.TaskCreate, user: schemas.User = Depends(utils.get_current_user),
                db: Session = Depends(get_DB), token: str =Security(api_key)):
    """
    this function adds task in db for user
    :param token:
    :param task:
    :param user:
    :param db:
    :return:
    """
    if_exist = crud.get_task_by_title(db=db, task_title=task.title, user_id=user.id)
    if if_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already exists"
        )
    crud.create_task(db, task=task, user_id=user.id)
    return {"message": "task added successfully"}


@app.get("/user/tasks/", response_model=List[schemas.Task], tags=["todo/get-tasks"])
def get_user_tasks(user: schemas.User = Depends(utils.get_current_user), db: Session = Depends(get_DB),
                   token: str =Security(api_key)):
    """
    this function returns tasks by specific user
    :param user:
    :param db:
    :return:
    """
    return crud.get_tasks_by_user(db, user_id=user.id)


@app.put("/user/task/{task_id}", response_model=dict, tags=["todo/update-tasks"])
async def update_task(task_id: int, user: schemas.User = Depends(utils.get_current_user),
                      task: schemas.TaskCreate = None, db: Session = Depends(get_DB),
                      token: str =Security(api_key)):
    """
    this function updates user task
    :param token:
    :param task_id:
    :param user:
    :param task:
    :param db:
    :return:
    """
    res = crud.update_task_by_user(db, user_id=user.id, task_id=task_id, task=task)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "task updated successfully"}


@app.delete("/user/task/{task_id}", response_model=dict, tags=["todo/delete-tasks"])
def delete_user_task(user: schemas.User = Depends(utils.get_current_user), task_id: int = 0,
                     db: Session = Depends(get_DB), token: str =Security(api_key)):
    """
    this function deletes a certain task by user
    :param user:
    :param task_id:
    :param db:
    :return:
    """
    res = crud.delete_task(db, user_id=user.id, task_id=task_id)
    if res != 1:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"Message": f"task is successfully deleted."}


@app.put("/user/complete-task/{task_id}", response_model=dict, tags=["todo/complete-tasks"])
def complete_task(user: schemas.User = Depends(utils.get_current_user), task_id: int = 0,
                  db: Session = Depends(get_DB), token:str=Security(api_key)):
    """
    changes status of user task
    :param user:
    :param task_id:
    :param db:
    :return:
    """
    res = crud.complete_task(db, user_id=user.id, task_id=task_id)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res


@app.get("/user/complete-tasks/", response_model=Union[List[schemas.Task], dict], tags=["todo/all-complete-tasks"])
def get_user_finished_tasks(user: schemas.User = Depends(utils.get_current_user), db: Session = Depends(get_DB),
                            token:str=Security(api_key)):
    """
    returns all the finished tasks
    :param user:
    :param db:
    :return:
    """
    res = crud.get_complete_tasks_by_user(db, user_id=user.id)
    if not res:
        raise HTTPException(status_code=404, detail="No completed task found")
    return res


@app.get("/user/due-today/", response_model=Union[List[schemas.Task], dict], tags=["todo/tasks-due-today"])
def get_user_due_today_tasks(user: schemas.User = Depends(utils.get_current_user), db: Session = Depends(get_DB),
                             token:str=Security(api_key)):
    """
    returns all the tasks due today
    :param user:
    :param db:
    :return:
    """
    res = crud.get_tasks_due_today(db, user_id=user.id)
    if not res:
        raise HTTPException(status_code=404, detail="No tasks due today.")
    return res
