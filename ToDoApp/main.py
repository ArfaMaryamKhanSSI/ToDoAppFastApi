import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session

import auth_email
import utils
import crud
import schemas
from database import get_DB

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/user/register/", tags=["users"], response_model=str)
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
    token = utils.encode_token(stored_user.email)
    # check if token already exists
    db_token = crud.get_token(db, user_id=stored_user.id)
    if not db_token:
        crud.create_token(db, token=token, user_id=stored_user.id)
        encrypted_token = utils.encrypt_token(token.access_token)
        token = encrypted_token.decode("utf-8")
        verification_link = f"http://localhost:8000/user/confirmation/{token}"
        background_tasks.add_task(auth_email.send_verification_email, token=verification_link, user_email=stored_user.email)
        return verification_link


@app.get("/user/confirmation/{token}", tags=["users"])
def confirmation(token: str, db: Session = Depends(get_DB)):
    """
    this function confirms the user
    :param token:
    :param db:
    :return:
    """
    token = token.encode("utf-8")
    decrypt_token = utils.decrypt_token(token)
    decoded_token = utils.decode_token(decrypt_token)
    if decoded_token:
        user = crud.get_user_by_email(db, decoded_token.get("email"))
        if user:
            res = crud.confirmed_user(db, user.email)
            if not res:
                crud.confirmation(db, user.email)
                return {"Message": "User Confirmed"}
            raise HTTPException(status_code=400, detail="User already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    raise HTTPException(status_code=400, detail="Token expired")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
