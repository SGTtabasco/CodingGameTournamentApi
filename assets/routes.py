from fastapi import APIRouter
import assets.users.routes as users


router = APIRouter()
router.include_router(users.router)
