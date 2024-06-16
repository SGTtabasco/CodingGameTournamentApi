from prisma.models import User
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import random
import string
import bcrypt
import datetime
from assets.users.token import validate_token_wrapper

router = APIRouter()


class UserLogin(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    code: int
    message: str
    token: str


class UserRegister(BaseModel):
    username: str
    password: str


class UserRegisterResponse(BaseModel):
    code: int
    message: str
    token: str


class TokenIn(BaseModel):
    token: str


class TokenOut(BaseModel):
    code: int
    message: str


def generate_token() -> str:
    """ Generate a token for the user
    :return: str (length=128)
    """
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
    return token


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user: UserLogin) -> UserLoginResponse:
    user_db = await User.prisma().find_unique(where={"username": user.username})  # Find user by username
    if user_db is None:  # If user not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not bcrypt.checkpw(user.password.encode(), user_db.password.encode()):  # Check if password is correct
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    # Generate token and update user's token and last_login
    token = generate_token()
    while await User.prisma().find_unique(where={"token": token}) is not None:  # Check if token already exists
        token = generate_token()
    await User.prisma().update(where={"username": user.username}, data={"token": token,
                                                                        "last_login": datetime.datetime.now()})
    return UserLoginResponse(code=status.HTTP_200_OK, message="Login successful", token=token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister) -> UserRegisterResponse:
    user_db = await User.prisma().find_unique(where={"username": user.username})
    if user_db is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    # Hash password
    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    token = generate_token()
    while await User.prisma().find_unique(where={"token": token}) is not None:  # Check if token already exists
        token = generate_token()
    await User.prisma().create(data={"username": user.username, "password": hashed_password, "token": token})

    return UserRegisterResponse(code=status.HTTP_201_CREATED, message="User registered successfully", token=token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: TokenIn) -> TokenOut:
    await validate_token_wrapper(token.token)  # Validate token / raise exception if invalid
    await User.prisma().update(where={"token": token.token}, data={"token": None})
    return TokenOut(code=status.HTTP_200_OK, message="Logout successful")


@router.post("/delete", status_code=status.HTTP_200_OK)
async def delete(token: TokenIn) -> TokenOut:
    await validate_token_wrapper(token.token)  # Validate token / raise exception if invalid
    await User.prisma().delete(where={"token": token.token})
    return TokenOut(code=status.HTTP_200_OK, message="User deleted successfully")
