from aiogram.dispatcher.filters.state import State, StatesGroup


class GiveAwayState(StatesGroup):
    user_id = State()
    name = State()


class GiveAwaySponsorState(StatesGroup):
    status_message_id = State()
    give_message_id = State()
    giveaway_id = State()
    data = State()


class GiveAwayMailing(StatesGroup):
    give_message_id = State()
    giveaway_id = State()
    name = State()
    message = State()