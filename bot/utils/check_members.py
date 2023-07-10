import asyncio
from logging import log
from loguru import logger
from aiogram.utils import exceptions
from aiogram import Bot

from bot.models import members


async def check_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    r = {'bad_user': False, 'member': False, 'error': None, 'user': None}
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except exceptions.ChatNotFound:
        logger.error(f"Target [ID:{user_id}]: invalid user ID")
        r['bad_user'] = True
    except exceptions.RetryAfter as e:
        logger.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await check_member(bot, chat_id, user_id)
    except exceptions.UserDeactivated:
        logger.error(f"Target [ID:{user_id}]: user is deactivated")
        r['bad_user'] = True
    except exceptions.TelegramAPIError as e:
        logger.error(
            "Target [ID:{user_id}]: failed | Err: {e}", user_id=user_id, e=e)
        if 'User not found' in str(e):
            r['bad_user'] = True
        else:
            logger.warning('New ERROR TG: {e}', e=e)
            r['bad_user'] = True
        r['error'] = e
    except asyncio.CancelledError:
        logger.warning('Задача [check_member(utils)] отменена, завершаем работу.')
    else:
        #logger.info(f"Target [ID:{user_id}]: success")
        if member.status == 'creator' or member.status == 'member':
            r['member'] = True
        elif member.status == 'left':
            r['member'] = False
        else:
            r['member'] = False
        r['user'] = member.user.to_python()
    return r
