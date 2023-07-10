from aiogram import Dispatcher
from aiogram.utils.executor import Executor
from tortoise import Tortoise, fields, run_async
from tortoise.models import Model
from tortoise.exceptions import OperationalError, IntegrityError
from bot import config

db = Tortoise()


class BaseModel(Model):
    class Meta:
        abstract = True


class TimedBaseModel(BaseModel):
    class Meta:
        abstract = True

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


async def on_startup(dispatcher: Dispatcher = None):
    try:
        await db.init(config=config.TORTOISE_ORM, _create_db=True)
    except OperationalError:
        await db.init(config=config.TORTOISE_ORM, _create_db=False)
    await Tortoise.generate_schemas()


async def on_shutdown(dispatcher: Dispatcher = None):
    # await db.get_connection('default').db_delete()
    await db.close_connections()


def setup(runner: Executor):
    runner.on_startup(on_startup)
    runner.on_shutdown(on_shutdown)
