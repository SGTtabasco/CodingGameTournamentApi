from prisma.models import User
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from assets.users.token import validate_token_wrapper
import random
import string
import assets.shared as shared
import os

router = APIRouter(prefix="/discord")


class RequestDiscordSync(BaseModel):
    token: str


class ResponseDiscordSync(BaseModel):
    code: int
    token_validation: str


class RequestDiscordJoinVC(BaseModel):
    token: str


class ResponseDiscordJoinVC(BaseModel):
    code: int
    message: str


@router.post("/sync", response_model=ResponseDiscordSync)
async def discord_sync(request: RequestDiscordSync) -> ResponseDiscordSync:
    user = await validate_token_wrapper(request.token)
    if user.discord_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a discord account linked")

    # create a temp discord token
    discord_token = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    await User.prisma().update(where={"token": request.token}, data={"discord_sync_token": discord_token})
    return ResponseDiscordSync(code=200, token_validation=discord_token)


@router.post("/join_vc", response_model=ResponseDiscordJoinVC)
async def discord_join_vc(request: RequestDiscordJoinVC) -> ResponseDiscordJoinVC:
    user = await validate_token_wrapper(request.token)
    if user.discord_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User does not have a discord account linked")
    guild = shared.client.get_guild(int(os.getenv('DISCORD_GUILD_ID')))
    channel = await guild.create_voice_channel(name=f"{user.username}'s Channel")
    discord_user = guild.get_member(int(user.discord_id))
    if not discord_user.voice:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not in a voice channel")

    await discord_user.edit(mute=True, voice_channel=channel, reason="User requested to join voice channel")
    return ResponseDiscordJoinVC(code=200, message="Connected to voice channel")


