import asyncio
from contextlib import suppress
import os
import re
from uuid import uuid4
import aiofiles
from loguru import logger
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import CommandHelp, CommandStart, Command, Text
from aiogram.types import chat_invite_link
from aiogram.utils.emoji import emojize, demojize
from aiogram import types, md
from aiogram.utils import exceptions as aiogram_exc
from aiogram.utils.mixins import T

from aiogram.utils.deep_linking import get_start_link
from aiogram.utils.deep_linking import decode_payload
from bot.handlers import giveaway

from bot.keyboards import buttons
from bot.misc import dp, bot
from bot import config, keyboards as kb, states as st, utils
from bot import models


@dp.message_handler(chat_type=[types.ChatType.PRIVATE], state='*', is_admin=True,
                    content_types=types.ContentType.DOCUMENT)
async def cmd_new_ids(message: types.Message, state: FSMContext):
    ids_filename = None
    new_ids = []
    try:
        command = message.caption_entities[0].get_text(message.caption)
    except Exception as e:
        logger.error('Err in cmd_new_ids: {e}', e=e)
    else:
        if command == '/new_ids':
            ids_filename = config.DATA_DIR / f"{uuid4().hex}.txt"
            doc = message.document
            file = await bot.get_file(doc.file_id)
            await bot.download_file(file.file_path, ids_filename)

    if ids_filename and os.path.exists(ids_filename):
        all_count = await models.TelegramUser.all().count()
        async for new_ids in utils.big_file_reader(ids_filename, 5000):
            if new_ids:
                users = []
                dups = await models.TelegramUser.filter(id__in=new_ids).values_list('id', flat=True)
                error = False
                for user_id in new_ids:
                    if user_id in dups:
                        continue
                    user = models.TelegramUser(id=user_id)
                    users.append(user)
                try:
                    await models.TelegramUser.bulk_create(users)
                except Exception as e:
                    logger.error('Err new user_ids bulk_create: {e}', e=e)
                    error = True
                finally:
                    new_ids = []
            else:
                break
    new_count = await models.TelegramUser.all().count()
    if all_count < new_count:
        await message.reply(f'Новые пользователи добавлены: {(new_count-all_count)}')
    elif all_count == new_count:
        text = 'Нет новых пользователей!' + ('Были ошибки при добавлении. ' if error else '')
        await message.reply(text)
    else:
        await message.reply('Не найдено новых ids. Возможно ошибка парсинга.')
