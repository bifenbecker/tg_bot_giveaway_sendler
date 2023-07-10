import asyncio
from loguru import logger
from aiogram import Bot
from aiogram.utils import exceptions


async def copy_message(bot: Bot,
                       chat_id: int,
                       user_id: int,
                       message_id: int) -> bool:
    """
    Safe messages sender
    :return:
    """
    r = {'bad_user': False, 'result': False, 'msg': None}
    try:
        r['msg'] = await bot.copy_message(user_id, chat_id, message_id)
    except exceptions.BotBlocked:
        logger.error(f"Target [ID:{user_id}]: blocked by user")
        r['bad_user'] = True
    except exceptions.ChatNotFound:
        logger.error(f"Target [ID:{user_id}]: invalid user ID")
        r['bad_user'] = True
    except exceptions.RetryAfter as e:
        logger.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await copy_message(bot, chat_id, user_id, message_id)  # Recursive call
    except exceptions.UserDeactivated:
        logger.error(f"Target [ID:{user_id}]: user is deactivated")
        r['bad_user'] = True
    except exceptions.TelegramAPIError as e:
        logger.error(
            "Target [ID:{user_id}]: failed | Err: {e}", user_id=user_id, e=e)
        r['result'] = False
        r['bad_user'] = True
    except asyncio.CancelledError:
        logger.warning(
            'Задача [send_message(utils)] отменена, завершаем работу.')
    else:
        logger.info(f"Target [ID:{user_id}]: success")
        r['result'] = True
    return r
