import typing
import asyncio
from aiogram.dispatcher import FSMContext
from aiogram import types
from aiogram.utils.deep_linking import get_start_link
from loguru import logger

from bot.misc import dp, bot
from bot import config, keyboards as kb
from bot import models
from bot import states as st
from bot import utils


@dp.callback_query_handler(kb.cbk.gway.filter(action='deeplnk'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_user_voite(query: types.CallbackQuery,
                              callback_data: typing.Dict[str, str],
                              state: FSMContext):
    current_state = await state.get_state()
    try:
        giveaway_id = int(callback_data['value'])
        link = await get_start_link(f'sid#{giveaway_id}', encode=True)
        msg = await query.message.answer(f'Ref-ссылка ГИВа: {link}')
        await query.answer("")
    except Exception as e:
        await query.answer('Ошибочка...')
        logger.error('Error in deep link create: {e}', e=e)
    else:
        await asyncio.sleep(15)
        await bot.delete_message(msg.chat.id, msg.message_id)


@dp.callback_query_handler(kb.cbk.gway.filter(action='finish'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_finish(query: types.CallbackQuery,
                              callback_data: typing.Dict[str, str],
                              state: FSMContext):
    current_state = await state.get_state()
    await query.answer('Гив ЗАВЕРШЕН!')
