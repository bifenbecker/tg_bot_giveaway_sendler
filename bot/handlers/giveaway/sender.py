import typing
import asyncio
from aiogram.dispatcher import FSMContext
from aiogram import types
from tortoise import exceptions as tortoise_exc
from aiogram.utils import exceptions as aiogram_exc
from loguru import logger

from bot.misc import dp, bot
from bot import config, keyboards as kb
from bot import models
from bot.models.sender import MailingUserListReport
from bot import states as st
from bot import utils
from bot.jobs import gdata, mail_sender

# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.gway.filter(action='sender'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_sender(query: types.CallbackQuery,
                          callback_data: typing.Dict[str, str],
                          state: FSMContext):

    giveaway_id = int(callback_data['value'])
    mailings = await models.Mailing.filter(giveaway_id=giveaway_id).values('id', 'name', 'status')
    mailings_count = len(mailings)
    if mailings_count == 0:
        await query.answer('Нет рассылок для данного гива!')
    else:
        await query.answer('')
    return await query.message.edit_reply_markup(
        reply_markup=kb.giveaway_sender_kb(giveaway_id, mailing_list=mailings)
    )


# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.sender.filter(action='add'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_sender_add(query: types.CallbackQuery,
                              callback_data: typing.Dict[str, str],
                              state: FSMContext):
    if (await state.get_state()):
        await state.finish()
    await st.GiveAwayMailing.name.set()
    await state.update_data(giveaway_id=int(callback_data['value']),
                            give_message_id=query.message.message_id)
    await query.answer("")
    await asyncio.sleep(.05)
    await query.message.answer('Придумайте название рассылки: ', reply_markup=kb.cancel_kb())
# ---------------------------------------------------------------------------------


@dp.message_handler(commands={'cancel'},
                    chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwayMailing, is_admin=True)
@dp.message_handler(lambda m: m.text == kb.btn.text_cancel,
                    chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwayMailing, is_admin=True)
async def giveaway_mailing_create_cancel(message: types.Message, state: FSMContext):
    logger.info('Admin [{user_id}] New give Cancel.',
                user_id=message.from_user.id)
    data = await state.get_data()
    giveaway_id = data['giveaway_id']
    mailings = await models.Mailing.filter(giveaway_id=giveaway_id).values('id', 'name', 'status')
    await state.finish()
    await message.answer('Создание рассылки отменено.', reply_markup=kb.main_keyboard())
    await asyncio.sleep(0.06)
    if (msg_id := data.get('give_message_id', None)):
        await bot.copy_message(message.from_user.id,
                               message.from_user.id,
                               msg_id,
                               reply_markup=kb.giveaway_sender_kb(giveaway_id, mailing_list=mailings))
    await asyncio.sleep(0.06)
    await bot.delete_message(message.from_user.id, msg_id)

# ---------------------------------------------------------------------------------


@dp.message_handler(chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwayMailing.name, is_admin=True)
async def giveaway_mailing_set_name(message: types.Message, state: FSMContext):
    logger.info('Admin [{user_id}] NEW mailing name check',
                user_id=message.from_user.id)

    if not message.text or len(message.text) > 190:
        text = 'Название не корректно! (Возможно вы превысили 190 символов!) Попробуйте снова:'
        return await message.answer(text)

    await state.update_data(name=message.text)
    await st.GiveAwayMailing.message.set()
    await message.answer('Добавьте сообщение для рассылки: ')
# ---------------------------------------------------------------------------------


@dp.message_handler(chat_type=[types.ChatType.PRIVATE],
                    state=st.GiveAwayMailing.message, is_admin=True, content_types=[types.ContentType.ANY])
async def giveaway_mailing_create(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        mailing = await models.Mailing.create(
            giveaway_id=data['giveaway_id'],
            name=data['name'],
            author_id=message.from_user.id,
            tg_message_id=message.message_id,
            status=models.Mailing.MStatus.wait
        )
    except tortoise_exc.IntegrityError as e:
        logger.error('Error create mailing: {e}', e=e)
        await message.answer('Не удалось создать рассылку')
    else:
        await state.finish()
        await message.answer('Рассылка успешно добавлена в ГИВ.',
                             reply_markup=kb.main_keyboard())
        await asyncio.sleep(0.05)
        await bot.copy_message(
            message.from_user.id,
            message.from_user.id,
            message.message_id,
            reply_markup=kb.giveaway_mailing_index_kb(
                mailing.id,
                data['giveaway_id'], default='start', excluded=mailing.exclude_members))
        if (msg_id := data.get('give_message_id', None)):
            await asyncio.sleep(0.05)
            await bot.delete_message(message.from_user.id, msg_id)
# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.sender.filter(action='mail-id'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_mailing_index(query: types.CallbackQuery,
                                 callback_data: typing.Dict[str, str],
                                 state: FSMContext):
    mailing = await models.Mailing.filter(id=int(callback_data['value'])).first()
    if not mailing:
        return await query.answer('Рассылка не найдена!')
    if mailing.status == mailing.MStatus.in_progress:
        default = 'stop'
    elif (mailing.status == mailing.MStatus.wait) or (mailing.status == mailing.MStatus.paused):
        default = 'start'
    else:
        default = 'finished'
    await bot.copy_message(
        query.from_user.id,
        mailing.author_id,
        mailing.tg_message_id,
        reply_markup=kb.giveaway_mailing_index_kb(
            mailing.id,
            mailing.giveaway_id,
            default=default,
            excluded=mailing.exclude_members
        )
    )
    await query.message.delete()

# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.gway.filter(action='from_to_sender'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_sender_index(query: types.CallbackQuery,
                                callback_data: typing.Dict[str, str],
                                state: FSMContext):
    giveaway_id = int(callback_data['value'])
    mailings = await models.Mailing.filter(giveaway_id=giveaway_id).values('id', 'name', 'status')

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
        await asyncio.sleep(0.06)
        try:
            await query.message.edit_text(text=text,
                                          reply_markup=kb.giveaway_sender_kb(
                                              giveaway_id, mailing_list=mailings)
                                          )
        except aiogram_exc.BadRequest:
            await query.message.edit_caption(caption=text,
                                             reply_markup=kb.giveaway_sender_kb(
                                                 giveaway_id, mailing_list=mailings)
                                             )
    else:
        await query.answer('FUCK!')

# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.sender.filter(action=['start', 'stop']),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_sender_start_and_stop(query: types.CallbackQuery,
                                         callback_data: typing.Dict[str, str],
                                         state: FSMContext):
    if gdata.MEMBERS_CHECK_WORK_NOW:
        return await query.answer(('В данный момент идет сбор участников! '
                                   'Дождитесь завершения и попробуйте еще раз.'),
                                  show_alert=True)
    if gdata.SENDER_WORK_NOW:
        text = 'Идет рассылка!'
        logger.info(text)
        return await query.answer(text, show_alert=True)
    elif gdata.CREATE_SENDER_BASE_WORK_NOW:
        return await query.answer('Создается база рассылки - подождите!')
    else:
        mailing_id = int(callback_data['value'])
        mailing = await models.Mailing.filter(id=mailing_id).first()
        if mailing and (mailing.status == mailing.MStatus.paused or
                        mailing.status == mailing.MStatus.wait):
            gdata.CREATE_SENDER_BASE_WORK_NOW = True
            try:
                if (await models.MailingUserListReport.filter(mailing_id=mailing_id).count()) == 0:
                    count = 10000
                    offset = 0
                    member_list = []
                    if mailing.exclude_members:
                        ct_model = await models.GiveAwayMemberCheckTimes\
                            .filter(giveaway_id=mailing.giveaway_id, finish=True)\
                            .order_by('-check_time').first()
                        if ct_model:
                            member_list = await models.GiveAwayMember.filter(
                                giveaway_id=mailing.giveaway_id,
                                checked_time__gte=ct_model.check_time
                            ).values_list('user__id', flat=True)
                        else:
                            return await query.answer(
                                ('Вам необходимо собрать пересечения, чтобы исключить их из рассылки.'
                                 'Запустите сбор пересечений, или сделайте рассылку по всей базе.'),
                                show_alert=True)

                    await query.answer(('Процесс запуска может занять несколько минут!'
                                        ' Для начала надо собрать базу!'), show_alert=True)

                    while True:
                        user_ids_query = models.TelegramUser.filter(
                            bot_mailing=True, bad=False)\
                            .filter(id__not_in=member_list).offset(offset).limit(count)
                        user_ids = await user_ids_query.values_list('id', flat=True)
                        reports = []
                        for user_id in user_ids:
                            mulr = MailingUserListReport(
                                mailing_id=mailing_id,
                                user_id=user_id,
                                status=MailingUserListReport.MRStatus.queued,
                                tg_message_id=mailing.tg_message_id
                            )
                            reports.append(mulr)
                        if reports:
                            await models.MailingUserListReport.bulk_create(reports)
                        if len(user_ids) < count:
                            break
                        offset += count
            finally:
                gdata.CREATE_SENDER_BASE_WORK_NOW = False

            mulr_query = models.MailingUserListReport.filter(
                mailing_id=mailing_id)
            users_count = await mulr_query.count()

            if users_count > 0:

                if (await mail_sender(bot, mailing_id, query.from_user)):
                    await query.message.answer((f'База рассылки создана. Количество: [{users_count}]\n'
                                                'Запустили рассылку!'))
            else:
                await mulr_query.delete()
                await query.message.answer(
                    'Не удалось создать базу рассылки! Нет пользователей для рассылки')
        elif mailing and mailing.status == mailing.MStatus.completed:
            await query.answer('Данная рассылка завершена!')
        elif mailing and mailing.status == mailing.MStatus.in_progress:
            await query.answer('Идет рассылка!')
        else:
            await query.answer('Рассылка не существует!')

# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.sender.filter(action=['exclude']),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_sender_exclude_members(query: types.CallbackQuery,
                                          callback_data: typing.Dict[str, str],
                                          state: FSMContext):
    mailing_id = int(callback_data['value'])
    mailing = await models.Mailing.filter(pk=mailing_id).first()
    if (mailing.status == mailing.MStatus.paused) or (mailing.status == mailing.MStatus.wait):
        default = 'start'
    elif mailing.status == mailing.MStatus.in_progress:
        default = 'stop'
    else:
        default = 'finished'
    if mailing.exclude_members:
        mailing.exclude_members = False
        text = 'Участники ГИВа будут включены в рассылку!'
    else:
        mailing.exclude_members = True
        text = 'Участники ГИВа будут исключены из рассылки!'
    await mailing.save()
    await query.message.edit_reply_markup(
        kb.giveaway_mailing_index_kb(
            mailing.id,
            mailing.giveaway_id,
            default=default,
            excluded=mailing.exclude_members
        ))
    await query.answer(text)

# ---------------------------------------------------------------------------------


@dp.callback_query_handler(kb.cbk.sender.filter(action='finished'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_mailing_index(query: types.CallbackQuery,
                                 callback_data: typing.Dict[str, str]):
    mailing_id = int(callback_data['value'])
    statuses = models.MailingUserListReport.MRStatus
    report_ok_count = await models.MailingUserListReport.filter(mailing_id=mailing_id,
                                                                status=statuses.success).count()
    report_err_count = await models.MailingUserListReport.filter(mailing_id=mailing_id,
                                                                 status=statuses.error).count()
    report_wait_count = await models.MailingUserListReport.filter(mailing_id=mailing_id,
                                                                  status=statuses.queued).count()
    if gdata.SENDER_WORK_NOW:
        status_text = "Работает.\n"
    else:
        status_text = "Завершена.\n"
    text = (f'Статус рассылки: {status_text}'
            f'Успешно отправлено: {report_ok_count}\n'
            f'Ошибка при отправке: {report_err_count}\n'
            f'Осталось отправить: {report_wait_count}')
    await query.answer(text, show_alert=True)


@dp.callback_query_handler(kb.cbk.sender.filter(action='stop'),
                           chat_type=[types.ChatType.PRIVATE],
                           is_admin=True, state='*')
async def giveaway_mailing_index(query: types.CallbackQuery,
                                 callback_data: typing.Dict[str, str]):
    mailing_id = int(callback_data['value'])
    await query.answer('Функция отсутстсвовала в ТЗ. Если желаете добавить - напишите разработчику.')
