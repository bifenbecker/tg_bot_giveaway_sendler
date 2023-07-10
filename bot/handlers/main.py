import asyncio
from contextlib import suppress
import re
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
from bot import config, keyboards as kb, states as st
from bot import models


@dp.message_handler(CommandStart(), chat_type=[types.ChatType.PRIVATE], state='*', is_admin=True)
async def cmd_start(message: types.Message, state: FSMContext):

    current_state = await state.get_state()
    if current_state:
        await state.finish()
    if (user := message.from_user).id in config.ADMIN_IDS:
        user_data = user.to_python()
        user_data['bot_admin'] = True
        user_data['bot_mailing'] = True
        await models.TelegramUser.get_or_create(defaults=user_data,
                                                pk=user.id)
        await message.answer('Добро пожаловать. Выберите действие: ', reply_markup=kb.main_keyboard())
    else:
        await message.answer('У вас нет доступа.')


@dp.message_handler(commands=['start'], chat_type=[types.ChatType.PRIVATE], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    args = message.get_args()
    payload = decode_payload(args)

    text = (
        'Поздравляем! Теперь вы зарегистрированы, как участник розыгрыша!\n'
        'Победитель будет выбран случайным образом с помощью этого бота. '
        'А также будет перевыбран, если окажется подписан не на все каналы.\n'
        'Итоги объявляются в этом боте и будут разосланы всем участникам.\n'
        'Желаем удачи✌️\n'
    )

    if not payload or payload.startswith('gid#'):
        user_data = message.from_user.to_python()
        user_data['bot_admin'] = False
        user_data['bot_mailing'] = True
        user_model, _ = await models.TelegramUser.get_or_create(
            defaults=user_data,
            pk=user_data['id']
        )
        giveaway_id = int(payload.removeprefix('gid#')) if payload else None
        if giveaway_id:
            member_data = dict(user=user_model, giveaway_id=giveaway_id)
            member = await models.GiveAwayMember.filter(**member_data).first()
            if member is None:
                member = await models.GiveAwayMember.create(**member_data)
                logger.warning('New User [{member}] is member NOW in GiveAway: [{giveaway_id}]',
                               member=user_model.username, giveaway_id=giveaway_id)
                return await message.answer(text)
            else:
                logger.warning('Member [{member}] is exists in GiveAway: [{giveaway_id}]',
                               member=user_model.username, giveaway_id=giveaway_id)
                #return await message.answer('Вы уже участвуете!')
                return await message.answer(text)
        else:

            return await message.answer(text)
