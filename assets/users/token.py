from prisma.models import User
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import datetime
import pytz

utc = pytz.UTC

router = APIRouter()


class TokenIn(BaseModel):
    token: str


class TokenOut(BaseModel):
    expires_in: int  # time before token expires


async def validate_token_wrapper(token: str) -> User:
    user = await User.prisma().find_unique(where={"token": token})
    if user is None or not await validate_token(token, user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


async def validate_token(token: str, user: User | None = None) -> bool:
    """ Validate the token
    :param user:
    :param token:
    :return: bool
    """
    if user is None:
        user = await User.prisma().find_unique(where={"token": token})
    if (user is None or (user.last_login + datetime.timedelta(days=1)).replace(tzinfo=utc) <
            datetime.datetime.now().replace(tzinfo=utc)):
        return False
    return True


@router.post("/validate", response_model=TokenOut)
async def validate(token_in: TokenIn) -> TokenOut:
    user = await User.prisma().find_unique(where={"token": token_in.token})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not await validate_token(token_in.token, user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Calculate time before token expires
    expires_in = ((user.last_login + datetime.timedelta(days=1)).replace(tzinfo=utc) -
                  datetime.datetime.now().replace(tzinfo=utc)).seconds
    return TokenOut(expires_in=expires_in)
