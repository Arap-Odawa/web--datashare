from fastapi import APIRouter
from chat_app.chat_app import chat_app_router


router = APIRouter()

router.include_router(chat_app_router)


