import typing
from enum import unique
from tortoise import fields
from tortoise.signals import post_delete, post_save, pre_delete, pre_save
from .db import BaseModel, TimedBaseModel


class GiveAwayMember(TimedBaseModel):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.TelegramUser', related_name='member_in')
    giveaway = fields.ForeignKeyField('models.GiveAway', related_name='members')
    checked_time = fields.DatetimeField(null=True)

    class Meta:
        unique_together = (
            ('user', 'giveaway'),
        )
        

