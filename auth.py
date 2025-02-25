from fastapi import Cookie, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Secret key and algorithm for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hardcoded user database with 5 test users
fake_users_db = {
    "user1": {
        "username": "user1",
        "full_name": "User One",
        "email": "user1@example.com",
        "hashed_password": bcrypt.hashpw("password1".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "disabled": False,
    },
    "user2": {
        "username": "user2",
        "full_name": "User Two",
        "email": "user2@example.com",
        "hashed_password": bcrypt.hashpw("password2".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "disabled": False,
    },
    "user3": {
        "username": "user3",
        "full_name": "User Three",
        "email": "user3@example.com",
        "hashed_password": bcrypt.hashpw("password3".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "disabled": False,
    },
    "user4": {
        "username": "user4",
        "full_name": "User Four",
        "email": "user4@example.com",
        "hashed_password": bcrypt.hashpw("password4".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "disabled": False,
    },
    "user5": {
        "username": "user5",
        "full_name": "User Five",
        "email": "user5@example.com",
        "hashed_password": bcrypt.hashpw("password5".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "disabled": False,
    },
}

# (This is used if you ever want to extract tokens from the Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_user(db, username: str):
    if username in db:
        return db[username]

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug(f"Token received: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWTError: {e}")
        raise credentials_exception
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception
    logger.debug(f"User retrieved: {user}")
    return user

# NEW: Dependency to get token from a cookie instead of an Authorization header.
def get_token_from_cookie(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return access_token
