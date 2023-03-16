from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
import os
import app.crud as crud
import app.schemas as schemas
from app.database import get_DB
from app.schemas import TokenBase

JWT_SECRET = os.environ.get('jwt_secret')
JWT_ALGORITHM = os.environ.get('jwt_algorithm')
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get('jwt_expiry')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_encryption_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("app/secret.key", "wb") as key_file:
        key_file.write(key)


def load_key():
    """
    Load the previously generated key
    """
    return open("app/secret.key", "rb").read()


def encode_token(email: str):
    """
    creates jwt token
    :param email:
    :return:
    """
    payload = {
        "email": email,
        "expiry": (datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))).timestamp()
    }
    token = jwt.encode(payload, key=JWT_SECRET, algorithm=JWT_ALGORITHM)
    return TokenBase(access_token=token, token_type="Bearer")


def decode_token(token: str):
    """
    decodes jwt token
    :param token:
    :return:
    """
    payload = jwt.decode(token, key=JWT_SECRET, algorithms=JWT_ALGORITHM)
    if payload.get("expiry") >= datetime.utcnow().timestamp():
        return payload
    return None


# password hashing
def hash_password(password):
    """
    creates hashed password
    :param password:
    :return:
    """
    return pwd_context.hash(password)


# verify password
def verify_password(hashed_password, plain_password):
    """
    verifies hashed password against plain password
    :param hashed_password:
    :param plain_password:
    :return:
    """
    return pwd_context.verify(plain_password, hashed_password)


# encrypt token
def encrypt_token(access_token: str):
    """
    encrypts token
    :param access_token:
    :return:
    """
    key = load_key()
    encoded_token = access_token.encode()
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(encoded_token)
    return encrypted_message


# decrypt token
def decrypt_token(enc_access_token: bytes):
    """
    decrypts token
    :param enc_access_token:
    :return:
    """
    key = load_key()
    fernet = Fernet(key)
    decrypted_token = fernet.decrypt(enc_access_token)
    decoded_token = decrypted_token.decode()
    return decoded_token


def create_token_link(db_user: schemas.User, db: Session = Depends(get_DB)):
    """
    This function first makes token (either create or update) then returns email link
    :param db_user:
    :param db:
    :return:
    """
    token = get_and_store_token(db_user=db_user, db=db)
    encrypted_token = encrypt_token(token.access_token)
    token = encrypted_token.decode("utf-8")
    verification_link = f"http://localhost:{os.environ.get('FASTAPI_PORT')}/confirmation/{token}"
    return verification_link


def get_and_store_token(db_user: schemas.User, db: Session = Depends(get_DB)):
    """
    this function makes token (either create or update) then returns
    :param db_user:
    :param db:
    :return:
    """
    token = encode_token(db_user.email)
    # check if token already exists
    db_token = crud.get_token(db, user_id=db_user.id)
    if not db_token:
        token = crud.create_token(db, token=token, user_id=db_user.id)
    else:
        if decode_token(db_token.access_token):
            token = crud.update_token(db, token=token, token_id=db_token.id)
    return token


# authenticate user
def authenticate_user(email: str, password: str, db_user: schemas.User):
    """
    This function verifies if user details input is correct
    :param email:
    :param password:
    :param db_user:
    :return:
    """
    if email == db_user.email and verify_password(hashed_password=db_user.password, plain_password=password):
        return db_user
    return False


async def get_current_user(req: Request, db: Session = Depends(get_DB)):
    """
    this func will return current user based on token value
    :param req:
    :param db:
    :return:
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    try:
        token = req.headers["Authorization"]
        token = token.split(" ")[1]
        payload = decode_token(token)
        if not payload:
            raise credentials_exception
        email: str = payload.get("email")
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user
