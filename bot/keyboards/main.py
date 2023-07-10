import typing
from aiogram import types
from aiogram.utils import emoji
from . import buttons as btn
from . import callbacks as cbk


InlineBtn = types.InlineKeyboardButton
Btn = types.KeyboardButton


def cancel_kb() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True).row(btn.cancel)


def main_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.insert(btn.create_giveaway)
    kb.insert(btn.all_giveaways)
    return kb


def giveaway_kb(give_away_id: int, sponsors_count: int = 0) -> types.ReplyKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)

    btn_sponsors_text = "Добавить спонсора" if sponsors_count == 0 else "Список спонсоров"
    btn_sponsors = InlineBtn(btn_sponsors_text, callback_data=cbk.sponsors.new(
        action='sponsors',
        value=give_away_id))
    kb.insert(btn_sponsors)

    if sponsors_count > 0:
        btn_deep_link = InlineBtn("Ref - ссылка", callback_data=cbk.gway.new(
            action='deeplnk',
            value=give_away_id))
        kb.insert(btn_deep_link)

        btn_sender = InlineBtn("Рассылки", callback_data=cbk.gway.new(
            action='sender',
            value=give_away_id))
        kb.insert(btn_sender)

        btn_members = InlineBtn("Пересечения (участники)", callback_data=cbk.gway.new(
            action='members',
            value=give_away_id))
        kb.insert(btn_members)

        # btn_finish = InlineBtn("Завершить ГИВ", callback_data=cbk.gway.new(
        #     action='finish',
        #     value=give_away_id))
        # kb.insert(btn_finish)

    return kb


def members_kb(give_away_id: int, last_check_time=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn_update = InlineBtn("Запустить новую проверку!", callback_data=cbk.gway.new(
        action='start_check_members',
        value=give_away_id))
    kb.insert(btn_update)
    if last_check_time:
        lct = last_check_time.strftime("%d/%m/%Y, %H:%M:%S")
        btn_download = InlineBtn(f"Участники [{lct}] (.txt)", callback_data=cbk.gway.new(
            action='download_members',
            value=give_away_id))
        kb.insert(btn_download)
    btn_back_to_give = InlineBtn('<< Назад', callback_data=cbk.gway.new(
        action='from_members_to_give',
        value=give_away_id))
    kb.insert(btn_back_to_give)
    return kb


def giveaway_list_nav_kb(index: int):
    kb = types.InlineKeyboardMarkup(row_width=2)
    back = InlineBtn(emoji.emojize(':back:'), callback_data=cbk.nav.new(
        action='givelist', value=f'{index-1}'))
    next = InlineBtn(emoji.emojize(':soon:'), callback_data=cbk.nav.new(
        action='givelist', value=f'{index+1}'))
    return kb.insert(back).insert(next)


def giveaway_sender_kb(giveaway_id: int, mailing_list: typing.List = []):
    kb = types.InlineKeyboardMarkup(row_width=1)

    for mailing in mailing_list:
        name = emoji.emojize(':email:') + " " + mailing['name']
        btn = InlineBtn(name, callback_data=cbk.sender.new(
            action='mail-id',
            value=mailing['id']))
        kb.insert(btn)

    btn_add = InlineBtn("Добавить рассылку", callback_data=cbk.sender.new(
        action='add',
        value=giveaway_id))
    kb.insert(btn_add)
    btn_back_to_give = InlineBtn('<< Назад', callback_data=cbk.gway.new(
        action='from_members_to_give',
        value=giveaway_id))
    kb.insert(btn_back_to_give)
    return kb


def giveaway_mailing_index_kb(mailing_id: int, giveaway_id: int = None, default='start', excluded=False):
    kb = types.InlineKeyboardMarkup(row_width=1)
    if default == 'start':
        btn_start = InlineBtn('Начать рассылку', callback_data=cbk.sender.new(action='start',
                                                                              value=mailing_id))
        kb.insert(btn_start)
    elif default == 'stop':
        btn_stop = InlineBtn('Остановить рассылку', callback_data=cbk.sender.new(action='stop',
                                                                                 value=mailing_id))
        kb.insert(btn_stop)
    if default != 'finished':
        em = emoji.emojize(":check_box_with_check:") if excluded else ""
        text = em + " Участники исключены" if excluded else "Рассылка по всей базе"
        btn_exclude = InlineBtn(text, callback_data=cbk.sender.new(
            action='exclude', value=mailing_id))
        kb.insert(btn_exclude)
    else:
        btn_finished = InlineBtn('РАССЫЛКА ЗАВЕРШЕНА', callback_data=cbk.sender.new(action='finished',
                                                                                 value=mailing_id))
        kb.insert(btn_finished)
    btn_back_to_mailing_list = InlineBtn('<< Назад', callback_data=cbk.gway.new(
        action='from_to_sender',
        value=giveaway_id))
    kb.insert(btn_back_to_mailing_list)
    
    if giveaway_id:
        btn_back_to_give = InlineBtn('<< Назад к ГИВу', callback_data=cbk.gway.new(
            action='from_members_to_give',
            value=giveaway_id))
        kb.insert(btn_back_to_give)
    return kb
