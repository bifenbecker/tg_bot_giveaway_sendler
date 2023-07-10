import typing
import asyncio
from aiogram import types, md


def get_author_name(user):
    return f'@{username}' \
        if (username :=
            user.username) else f"id{user.id}"


def page_giveaway_in(author: str,
                     give_id: int,
                     give_name: str,
                     status: bool = True,
                     sponsors_count: int = 0,
                     winner: typing.Optional[str] = None):
    """
    Создает шаблон поста для каждого гива
    """

    status = "Активен" if status else "Завершен"
    winner = winner or " - "

    return (
        f"#{'-'*60}\n\n"
        f"GiveAway № {md.hbold(give_id)} \n"
        f"Название: {md.hitalic(give_name)}\n"
        f"Автор: {author}\n"
        f"Статус: {md.hitalic(status)}\n\n"
        f"Проверенных спонсоров: {sponsors_count}\n"
        # f"Победители: {winner}\n"
        "\n"
        f"#{'-'*60}\n"
    )