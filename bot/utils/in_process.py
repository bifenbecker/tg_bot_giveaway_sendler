import asyncio
from bot import models
from bot.models import db
from loguru import logger

def run_in_process_reports(loop, mailing_id, msg_id):
    async def create_reports():
        try:
            # await db.on_startup()
            exist_ids = await models.MailingUserListReport.filter(mailing_id=mailing_id).values_list('user__id', flat=True)
            count = 5000
            offset = 0
            r_count = 0
            while True:
                logger.info('OK BLA!')
                user_ids_query = models.TelegramUser.filter(
                    bot_mailing=True, bad=False, id__not_in=exist_ids).offset(offset).limit(count)
                user_ids = await user_ids_query.values_list('id', flat=True)
                reports = []
                for user_id in user_ids:
                    mulr = models.MailingUserListReport(
                        mailing_id=mailing_id,
                        user_id=user_id,
                        status=models.MailingUserListReport.MRStatus.queued,
                        tg_message_id=msg_id
                    )
                    reports.append(mulr)
                    r_count += 1
                if reports:
                    await models.MailingUserListReport.bulk_create(reports)
                if len(user_ids) < count:
                    break
                offset += count
            logger.warning(f'CReated: {r_count}')
        except Exception as e:
            logger.error('Err: {e}', e=e)
        finally:
            pass
            # await db.on_shutdown()
        return 'YES'
    loop.run_until_complete(create_reports())
