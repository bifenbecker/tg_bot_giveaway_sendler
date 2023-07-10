import asyncio
from functools import partial
from aiogram import Bot, types
from loguru import logger
from tortoise import timezone as tortoise_tz
from bot import models
from bot.models.sender import Mailing
from bot.scheduler import scheduler
from bot.utils.sender import copy_message
from . import gdata

MReportModel = models.MailingUserListReport


async def mail_sender(bot: Bot, mailing_id: int, from_user: types.User):

    SENDERS = 0

    async def _notification():
        while True:
            if SENDERS == 0:
                msg = await bot.send_message(from_user.id, "Рассылка завершена!")
                break
            await asyncio.sleep(.05)

    async def _msender_job():
        try:

            mailing = await models.Mailing.get(pk=mailing_id)
            mailing.status = mailing.MStatus.in_progress
            await mailing.save()

            offset = 0
            count = 15

            while True:
                if SENDERS > 20:
                    await asyncio.sleep(0.01)
                    continue

                objects = await MReportModel.filter(mailing=mailing,
                                                    status=MReportModel.MRStatus.queued)\
                    .prefetch_related('user')\
                    .offset(offset)\
                    .limit(count)

                for mobj in objects:
                    user_id = mobj.user.id

                    async def send_user_message(obj, uid):
                        nonlocal SENDERS
                        SENDERS += 1
                        try:
                            r = await copy_message(bot,
                                                   mailing.author_id,
                                                   uid,
                                                   mailing.tg_message_id)
                            await asyncio.sleep(10)
                            if r['result']:
                                obj.status = mobj.MRStatus.success
                            else:
                                obj.status = mobj.MRStatus.error
                                obj.user.bad = True
                            await obj.save(force_update=True)
                        except Exception as e:
                            logger.error("Err: {e}", e=e)
                        finally:
                            SENDERS -= 1

                    job = scheduler.add_job(
                        partial(send_user_message, mobj, user_id), name='job_send_user_message', max_instances=21)

                    await asyncio.sleep(.05)  # 20 per second

                offset += count
                if len(objects) < count:
                    break

        except asyncio.CancelledError:
            logger.warning('Задача отменена, завершаем работу.')
            mailing.status = mailing.MStatus.paused
            await mailing.save()

        else:
            mailing.status = mailing.MStatus.completed
            await mailing.save()

        finally:
            gdata.SENDER_WORK_NOW = False
            scheduler.add_job(_notification, name='job_sender_notify')

    if not gdata.SENDER_WORK_NOW:
        scheduler.add_job(_msender_job, name='job_sender')
        gdata.SENDER_WORK_NOW = True
        return True
    else:
        return False
