from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from jose import jwt
from decouple import config
from passlib.context import CryptContext

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
