import asyncio
from aiogram.dispatcher import FSMContext
from aiogram import types
from tortoise import exceptions as tortoise_exc
from loguru import logger

from bot.misc import dp, bot
from bot import config, keyboards as kb
from bot import models
from bot import states as st
from bot import utils


# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------


@dp.message_handler(lambda m: m.text == kb.btn.text_create_giveaway,
                    is_admin=True,
                    chat_type=[types.ChatType.PRIVATE],)
async def new_giveaway_start(message: types.Message, state: FSMContext):
    logger.info('Admin [{user_id}] New give start.',
                user_id=message.from_user.id)
    await st.GiveAwayState.name.set()
    async with state.proxy() as data:
        data['user_id'] = message.from_user.id
    await message.answer('Как называется розыгрыш? ',
                         reply_markup=kb.cancel_kb())

# ---------------------------------------------------------------------------------


@dp.message_handler(commands={'cancel'},
                    chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwayState.name, is_admin=True)
@dp.message_handler(lambda m: m.text == kb.btn.text_cancel,
                    chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwayState.name, is_admin=True)
async def giveaway_set_name_cancel(message: types.Message, state: FSMContext):
    logger.info('Admin [{user_id}] New give Cancel.',
                user_id=message.from_user.id)
    await state.finish()
    await message.answer('Создание розыгрыша отменено.', reply_markup=kb.main_keyboard())


# ---------------------------------------------------------------------------------


@dp.message_handler(state=st.GiveAwayState.name,
                    is_admin=True,
                    chat_type=[types.ChatType.PRIVATE])
async def giveaway_set_name(message: types.Message, state: FSMContext):
    logger.info('Admin [{user_id}] New give name set: [{name}]',
                user_id=message.from_user.id,
                name=message.text)
    try:
        give = await models.GiveAway.create(name=message.text,
                                            author_id=message.from_user.id)
    except tortoise_exc.IntegrityError as e:
        logger.error('Error set give name: {e}', e=e)
        await message.answer('Такое название розыгрыша уже существует, попробуйте другое!')
    else:
        await state.finish()
        await st.GiveAwaySponsorState.data.set()

        author = utils.get_author_name(message.from_user)
        giveaway_text = utils.page_giveaway_in(author, give.id, give.name)
        msg_give = await message.answer(giveaway_text, reply_markup=kb.giveaway_kb(give.id))
        await asyncio.sleep(0.2)
        await msg_give.answer('Успешно! Теперь пришлите каналы участники.',
                              reply_markup=kb.cancel_kb())

        async with state.proxy() as data:
            data['giveaway_id'] = give.id
            data['give_message_id'] = msg_give.message_id


# ---------------------------------------------------------------------------------
