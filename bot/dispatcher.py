from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import AsyncSession

from models import engine

from config import TOKEN


bot = Bot(token = TOKEN, parse_mode = "HTML")
dp = Dispatcher(bot, storage = MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

Session = sessionmaker(
    engine, expire_on_commit = False, class_ = AsyncSession, autoflush = False
)
