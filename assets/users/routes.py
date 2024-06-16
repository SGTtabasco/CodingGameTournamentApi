from fastapi import APIRouter
import assets.users.login as login
import assets.users.token as token
import assets.users.discord as discord
router = APIRouter(prefix="/users")
router.include_router(login.router)
router.include_router(token.router)
router.include_router(discord.router)

