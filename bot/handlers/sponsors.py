from contextlib import suppress
from os import stat
import typing
import asyncio
import aiogram

from aiogram.dispatcher import FSMContext
from aiogram.types import message
from aiogram.utils.emoji import emojize, demojize
from aiogram import types, md
from tortoise import exceptions as tortoise_exc, functions as tfunc
from tortoise.query_utils import Prefetch
from aiogram.utils import exceptions as aiogram_exc
from loguru import logger

from bot.misc import dp, bot
from bot import config, keyboards as kb
from bot import models
from bot import states as st
from bot import utils


# ---------------------------------------------------------------------------------


@dp.message_handler(commands={'cancel'},
                    chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwaySponsorState.data)
@dp.message_handler(lambda m: m.text == kb.btn.text_cancel,
                    chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwaySponsorState.data)
async def add_sponsor_to_giveaway_cancel(message: types.Message, state: FSMContext):
    logger.info('Admin [{user_id}] Add sponsor Cancel.',
                user_id=message.from_user.id)
    data = await state.get_data()
    await bot.delete_message(message.chat.id, data['give_message_id'])
    await asyncio.sleep(0.2)
    if giveaway := (await models.GiveAway
                    .filter(pk=data['giveaway_id'])
                    .prefetch_related('sponsors', 'author')
                    .first()):
        sp_count = len(giveaway.sponsors)
        if sp_count > 0:
            await message.answer('Спонсоры успешно добавлены.', reply_markup=kb.main_keyboard())
        else:
            await message.answer('Вы можете добавить спонсоров позже.', reply_markup=kb.main_keyboard())
        text = utils.page_giveaway_in(
            author=(giveaway.author.username or f'ID: {giveaway.author.id}'),
            give_id=giveaway.id,
            give_name=giveaway.name,
            sponsors_count=sp_count
        )
        await asyncio.sleep(0.2)
        await message.answer(text=text,
                             reply_markup=kb.giveaway_kb(giveaway.id,
                                                         sponsors_count=sp_count))
    await state.finish()


# ---------------------------------------------------------------------------------


@dp.message_handler(state=st.GiveAwaySponsorState.data,
                    is_admin=True,
                    chat_type=[types.ChatType.PRIVATE])
async def add_sponsor_to_giveaway(message: types.Message, state: FSMContext):
    data = await state.get_data()
    logger.info('Admin [{user_id}] Add sponsor to GiveAway ID: [{give_id}]',
                user_id=message.from_user.id,
                give_id=data['giveaway_id'])

    mentions = utils.get_mentions(message)
    checked_mentions = await utils.check_chat_mentions(mentions, bot, True)
    checked_sponsors = [s for x in checked_mentions if (
        (s := x.get('chat', None)) and x['is_admin'])]
    # -----------------------------------
    added_sponsors = []
    for sponsor in checked_sponsors:
        model, _ = await models.TelegramChat.get_or_create(defaults=sponsor, pk=sponsor['id'])
        try:
            sponsor_model = await models.GiveAwaySponsor.create(
                giveaway_id=data['giveaway_id'],
                username=sponsor['username'],
                chat_id=model.id,
                ok_permissions=True
            )
        except Exception as e:
            sponsor_model = await models.GiveAwaySponsor.filter(giveaway_id=data['giveaway_id'],
                                                                chat_id=model.id).first()
            if sponsor_model:
                logger.warning('Sponsor [{name}] exists!',
                               name=(sponsor_model.username or sponsor_model.id))
            else:
                logger.error('Error in add sponsor: {e}', e=e)
        else:
            added_sponsors.append(sponsor_model.username)
            logger.info('Sponsor [{name}] added!', name=(
                sponsor_model.username or sponsor_model.id))
    # -----------------------------------

    if giveaway := (await models.GiveAway
                    .filter(pk=data['giveaway_id'])
                    .prefetch_related('sponsors', 'author')
                    .first()):
        sp_count = len(giveaway.sponsors)
        text = utils.page_giveaway_in(
            author=(giveaway.author.username or f'ID: {giveaway.author.id}'),
            give_id=giveaway.id,
            give_name=giveaway.name,
            sponsors_count=sp_count
        )
        msg_give = await message.answer(text=text,
                                        reply_markup=kb.giveaway_kb(giveaway.id,
                                                                    sponsors_count=sp_count))
        await state.update_data(give_message_id=msg_give.message_id)
        await asyncio.sleep(0.2)
        if added_sponsors:
            text = (
                f'Спонсоры успешно добавлены [{len(added_sponsors)}]! \n'
                'Пришлите спонсоров или нажмите Отмена.'
            )
            await msg_give.answer(text)

        else:
            if mentions and not checked_sponsors:
                text = (
                    'Спонсоры не прошли проверку! '
                    'Пришлите спонсоров или нажмите Отмена.'
                )
            elif mentions and checked_sponsors:
                text = (
                    'Нет новых спонсоров! '
                    'Пришлите спонсоров или нажмите Отмена.'
                )
            else:
                text = (
                    'Спонсоры не найдены! '
                    'Пришлите спонсоров или нажмите Отмена.'
                )

            await msg_give.answer(text)
        await asyncio.sleep(0.2)
        await bot.delete_message(message.chat.id, data['give_message_id'])

# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.sponsors.filter(action='sponsors'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_user_voite(query: types.CallbackQuery,
                              callback_data: typing.Dict[str, str],
                              state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        if current_state == 'GiveAwaySponsorState:data':
            await query.answer('Пришлите спонсоров или нажмите Отмена')
        else:
            pass
    else:
        if giveaway := (await models.GiveAway
                        .filter(pk=int(callback_data['value']))
                        .prefetch_related('sponsors', 'author')
                        .first()):
            if len(giveaway.sponsors) == 0:
                await st.GiveAwaySponsorState.data.set()
                await query.answer('')
                await asyncio.sleep(0.2)
                async with state.proxy() as data:
                    data['giveaway_id'] = giveaway.id
                    data['give_message_id'] = query.message.message_id
                await query.message.answer('Пришлите каналы участники:',
                                           reply_markup=kb.cancel_kb())
            else:
                sponsors = ",\n".join(
                    [" "*3 + (f'@{s.username}' or f'ID: {s.id}') for s in giveaway.sponsors])
                await query.answer(f'Спонсоры ГИВа: \n{sponsors}', show_alert=True)
