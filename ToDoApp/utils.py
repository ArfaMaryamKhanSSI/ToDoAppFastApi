from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from fastapi import Depends
from jose import jwt
from decouple import config
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_DB
from schemas import TokenBase

JWT_SECRET = config('secret')
JWT_ALGORITHM = config('algorithm')
ACCESS_TOKEN_EXPIRE_MINUTES = config('expiry')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_encryption_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)


def load_key():
    """
    Load the previously generated key
    """
    return open("secret.key", "rb").read()


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


def create_token_link(*, db_user: schemas.User, db: Session = Depends(get_DB)):
    """
    This function first makes token (either create or update) then returns email link
    :param db_user:
    :param db:
    :return:
    """
    token = get_and_store_token(db_user=db_user, db=db)
    encrypted_token = encrypt_token(token.access_token)
    token = encrypted_token.decode("utf-8")
    verification_link = f"http://localhost:8000/confirmation/{token}"
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
