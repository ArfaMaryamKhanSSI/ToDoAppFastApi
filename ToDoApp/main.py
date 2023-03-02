from typing import Union
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Body, BackgroundTasks, Request
from sqlalchemy.orm import Session
from starlette import status
import auth_email
import utils
import crud
import schemas
from database import get_DB

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/register/", tags=["todo/signup"], response_model=dict)
async def register(*, user: schemas.UserCreate = Body(default=None), db: Session = Depends(get_DB),
                   background_tasks: BackgroundTasks):
    """
    This function adds the user in DB and sends a verification email
    :param user:
    :param db:
    :param background_tasks:
    :return:
    """
    db_user = crud.get_user_by_email(db, user_email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = utils.hash_password(user.password)
    user_db = schemas.UserCreate(email=user.email, name=user.name, password=hashed_password)
    stored_user = crud.create_user(db=db, user=user_db)
    verification_link = utils.create_token_link(db_user=stored_user, db=db)
    background_tasks.add_task(auth_email.send_verification_email, token=verification_link,
                              user_email=stored_user.email)
    return {"message": "please confirm your account on this link", "link": verification_link}


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
async def login(*, req: Request, user: schemas.UserLogin = None, db: Session = Depends(get_DB),
                background_tasks: BackgroundTasks):
    """
    this func returns token if user is confirmed else it returns confirmation link
    :param req:
    :param user:
    :param db:
    :param background_tasks:
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
        background_tasks.add_task(auth_email.send_verification_email, token=verification_link,
                                  user_email=db_user.email)
        return {"message": "please confirm your account on this link", "link": verification_link}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
