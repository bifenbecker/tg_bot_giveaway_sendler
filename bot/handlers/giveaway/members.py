import typing
import asyncio
import aiofiles
from aiogram.dispatcher import FSMContext
from aiogram import types, exceptions as aiogram_exc
from loguru import logger
from bot.misc import dp, bot
from bot import config, keyboards as kb
from bot import models
from bot import utils
from bot.jobs import gdata, check_give_members


@dp.callback_query_handler(kb.cbk.gway.filter(action='members'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_members(query: types.CallbackQuery,
                           callback_data: typing.Dict[str, str],
                           state: FSMContext):
    giveaway_id = int(callback_data['value'])
    if gdata.SENDER_WORK_NOW:
        return await query.answer(('В данный момент работает рассылка! '
                                   'Дождитесь завершения и попробуйте еще раз.'),
                                  show_alert=True)
    if gdata.MEMBERS_CHECK_WORK_NOW:
        ct_model = await models.GiveAwayMemberCheckTimes\
            .filter(giveaway_id=giveaway_id, finish=False).first()
        if ct_model:
            checked_count = await models.TelegramUser\
                .filter(updated_at__gte=ct_model.check_time).count()

            members_count = await models.GiveAwayMember.filter(
                giveaway_id=giveaway_id,
                checked_time__gte=ct_model.check_time
            ).count()

            all_count = await models.TelegramUser\
                .filter(updated_at__lt=ct_model.check_time, bad=False).count()

            text = (
                'Идет проверка! Статистика: \n'
                f'Проверено: [{checked_count}]\n'
                f'Участников: [{members_count}]\n'
                f'Осталось проверить: [{all_count}]'
            )
        else:
            text = 'Идет проверка!'
        logger.info(text)
        await query.answer(text, show_alert=True)
    else:
        ct_model = await models.GiveAwayMemberCheckTimes\
            .filter(giveaway=giveaway_id, finish=True).order_by('-check_time').first()
        if not ct_model:
            if (await check_give_members(bot, giveaway_id, query.from_user)):
                logger.info(
                    f'Запустили сбор пересечений! GiveAway: [{giveaway_id}]')
                await query.answer('Запустили проверку!')
            else:
                await query.answer('Возникла какая то ошибка! Напишите разработчику!')
        else:
            if giveaway := (await models.GiveAway
                            .filter(pk=giveaway_id)
                            .prefetch_related('sponsors', 'author')
                            .first()):
                sp_count = len(giveaway.sponsors)
                text = utils.page_giveaway_in(
                    author=utils.get_author_name(giveaway.author),
                    give_id=giveaway.id,
                    give_name=giveaway.name,
                    sponsors_count=sp_count
                )
                await asyncio.sleep(0.2)
                try:
                    await query.message\
                        .edit_text(text=text,
                                   reply_markup=kb.members_kb(giveaway.id,
                                                              last_check_time=ct_model.check_time))
                except aiogram_exc.BadRequest:
                    await query.message\
                        .edit_caption(caption=text,
                                      reply_markup=kb.members_kb(giveaway.id,
                                                                 last_check_time=ct_model.check_time))


@dp.callback_query_handler(kb.cbk.gway.filter(action='from_members_to_give'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def from_members_to_give(query: types.CallbackQuery,
                               callback_data: typing.Dict[str, str],
                               state: FSMContext):
    giveaway_id = int(callback_data['value'])
    if giveaway := (await models.GiveAway
                    .filter(pk=giveaway_id)
                    .prefetch_related('sponsors', 'author')
                    .first()):
        sp_count = len(giveaway.sponsors)
        text = utils.page_giveaway_in(
            author=utils.get_author_name(giveaway.author),
            give_id=giveaway.id,
            give_name=giveaway.name,
            sponsors_count=sp_count
        )
        await asyncio.sleep(0.2)
        try:
            await query.message.edit_text(text=text,
                                          reply_markup=kb.giveaway_kb(giveaway.id,
                                                                      sponsors_count=sp_count))
        except aiogram_exc.BadRequest:
            await query.message.edit_caption(caption=text,
                                             reply_markup=kb.giveaway_kb(giveaway.id,
                                                                         sponsors_count=sp_count))


@dp.callback_query_handler(kb.cbk.gway.filter(action='start_check_members'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def start_members_check(query: types.CallbackQuery,
                              callback_data: typing.Dict[str, str],
                              state: FSMContext):
    giveaway_id = int(callback_data['value'])
    if gdata.SENDER_WORK_NOW:
        return await query.answer(('В данный момент работает рассылка! '
                                   'Дождитесь завершения и попробуйте еще раз.'),
                                  show_alert=True)
    if gdata.MEMBERS_CHECK_WORK_NOW:
        ct_model = await models.GiveAwayMemberCheckTimes\
            .filter(giveaway_id=giveaway_id, finish=False).first()
        if ct_model:
            checked_count = await models.TelegramUser\
                .filter(updated_at__gte=ct_model.check_time).count()

            members_count = await models.GiveAwayMember.filter(
                giveaway_id=giveaway_id,
                checked_time__gte=ct_model.check_time
            ).count()

            all_count = await models.TelegramUser\
                .filter(updated_at__lt=ct_model.check_time, bad=False).count()

            text = (
                'Идет проверка! Статистика: \n'
                f'Проверено: [{checked_count}]\n'
                f'Участников: [{members_count}]\n'
                f'Осталось проверить: [{all_count}]'
            )
        else:
            text = 'Идет проверка!'
        logger.info(text)
        await query.answer(text, show_alert=True)
    else:
        if (await check_give_members(bot, giveaway_id, query.from_user)):
            logger.info(
                f'Запустили сбор пересечений! GiveAway: [{giveaway_id}]')
            await query.answer('Запустили проверку!')
        else:
            await query.answer('Возникла какая то ошибка! Напишите разработчику!')


@dp.callback_query_handler(kb.cbk.gway.filter(action='download_members'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def download_members(query: types.CallbackQuery,
                           callback_data: typing.Dict[str, str],
                           state: FSMContext):

    giveaway_id = int(callback_data['value'])

    logger.info(f"Export giveaway id[{giveaway_id}] members. Txt file... ")

    members_data = await models.GiveAwayMember.filter(
        giveaway_id=giveaway_id).prefetch_related('user')\
        .values_list('user__first_name',
                     'user__last_name', 'user__username', 'user__id')

    filename = config.DATA_DIR / f'giveaway_{giveaway_id}_members.txt'

    try:
        async with aiofiles.open(filename, 'w', encoding='utf8') as f:
            await f.write('pid,firstname,lastname,username,userid\n')
            for index, member in enumerate(members_data):
                await f.write(f"{index+1}," + ",".join([
                    str(x) if x else "" for x in member]
                ) + "\n")

    except Exception as e:
        logger.error("Export txt error: {error}", error=e)
        return await query.answer('Невозможно экспортировать файл.')
    finally:
        del members_data
    await query.answer("Загружаем файл!")
    await types.ChatActions.upload_document()
    await query.message.answer_document(types.InputFile(filename))
