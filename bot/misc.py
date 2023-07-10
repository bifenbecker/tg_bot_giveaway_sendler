import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.utils.executor import Executor

from bot import config, utils
from bot.scheduler import setup as scheduler_setup

bot = Bot(config.TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)

storage = RedisStorage2(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    password=config.REDIS_PASSWORD,
    db=config.REDIS_FSM_DB,
    prefix=config.REDIS_FSM_PREFIX,
)
dp = Dispatcher(bot, storage=storage)
runner = Executor(dp, skip_updates=config.SKIP_UPDATES)
    


def setup():
    from bot.models import db, TelegramUser
    from bot import middlewares
    from bot import filters

    db.setup(runner)
    middlewares.setup(dp)
    filters.setup(dp)
    scheduler_setup(runner)

    import bot.handlers

