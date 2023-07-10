import asyncio
from aiogram import Bot, types
from loguru import logger
from tortoise import timezone as tortoise_tz
from bot import models
from bot.scheduler import scheduler
from bot.utils.check_members import check_member
from . import gdata

LOCKER = asyncio.Lock()


async def check_give_members(bot: Bot, giveaway_id, from_user: types.User):

    CHECKERS = 0

    async def _notification():
        while True:
            if CHECKERS == 0:
                msg = await bot.send_message(from_user.id, "Пересечения собраны!")
                break
            await asyncio.sleep(.05)


    async def check_and_update(new_check_time, chat_ids, user):
        nonlocal CHECKERS
        CHECKERS += 1
        try:
            member_data = None
            user_data = None
            for chat_id in chat_ids:
                r = await check_member(bot, chat_id, user.id)
                if r['user']:
                    user_data = r['user']
                if r['member']:
                    member_data = dict(
                        user_id=user.id,
                        giveaway_id=giveaway_id,
                        checked_time=new_check_time.check_time
                    )
                    await asyncio.sleep(.05)
                else:
                    member_data = None
                    if r['bad_user']:
                        user.bad = True
                        await user.save()
                        member = await models.GiveAwayMember\
                            .filter(user__id=user.id, giveaway__id=giveaway_id).first()
                        if member:
                            await member.delete()
                    break
            if user_data:
                user.update_from_dict(user_data)
                await user.save(force_update=True)

            if member_data:
                member, created = await models.GiveAwayMember.get_or_create(
                    defaults=member_data,
                    user__id=user.id,
                    giveaway__id=giveaway_id
                )
                if not created:
                    member.checked_time = new_check_time.check_time
                    await member.save()
                else:
                    logger.info('Detected new GiveAway: [{give}] member: [{member}]',
                                give=giveaway_id, member=user.id)
            else:
                logger.info('User checked! GiveAway: [{give}] member: [{member}]',
                                give=giveaway_id, member=user.id)

        except asyncio.CancelledError:
            logger.warning(
                'Задача [check_and_update] отменена, завершаем работу.')
        finally:
            CHECKERS -= 1

    async def _check_members_job():
        try:
            not_finished = await models.GiveAwayMemberCheckTimes.filter(finish=False)
            for nf in not_finished:
                await nf.delete()

            new_check_time = await models.GiveAwayMemberCheckTimes.create(
                giveaway_id=giveaway_id,
                check_time=tortoise_tz.now()
            )

            giveaway = await models.GiveAway.filter(id=giveaway_id).prefetch_related('sponsors').first()

            if not giveaway:
                logger.error('Give not found!')
                return False

            chat_ids = [x.chat_id for x in giveaway.sponsors]
            offset = 0
            count = 15

            for i in range(1, 27):
                if (x := len(chat_ids)*i) < 25:
                    count = x
                else:
                    break

            logger.warning(f'Check count in one query: [{count}]')

            while True:
                if CHECKERS > 25:
                    await asyncio.sleep(0.01)
                    continue

                users = await models.TelegramUser.filter(bot_mailing=True, bad=False)\
                    .offset(offset).limit(count)

                for user in users:
                    async def check_update_job():
                        try:
                            await check_and_update(new_check_time, chat_ids, user)
                        except Exception as e:
                            logger.error("Err: {e}", e=e)

                    job = scheduler.add_job(
                        check_update_job, name='job_check_update_job', max_instances=21)

                    await asyncio.sleep(.05)  # 20 per second
                logger.warning(f'Checkers count: [{CHECKERS}]')

                offset += count
                if len(users) < count:
                    break
                logger.warning('Checked count: {o}', o=offset)

            new_check_time.finish = True
            await new_check_time.save()

        except Exception as e:
            logger.error('Err: {e}', e=e)

        except asyncio.CancelledError:
            logger.warning(
                'Задача [check_members] отменена, завершаем работу.')

        finally:
            gdata.MEMBERS_CHECK_WORK_NOW = False
            scheduler.add_job(_notification, name='job_check_members_notify')

    if not gdata.MEMBERS_CHECK_WORK_NOW:
        scheduler.add_job(_check_members_job, name='job_check_members')
        gdata.MEMBERS_CHECK_WORK_NOW = True
        return True
    else:
        return False
