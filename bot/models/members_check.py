import typing
from enum import unique
from tortoise import fields
from tortoise.signals import post_delete, post_save, pre_delete, pre_save
from .db import BaseModel, TimedBaseModel


class GiveAwayMemberCheckTimes(TimedBaseModel):
    id = fields.IntField(pk=True)
    check_time = fields.DatetimeField(null=False)
    giveaway = fields.ForeignKeyField(
        'models.GiveAway', related_name='members_check_times', null=False)
    finish = fields.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('check_time', 'giveaway'),
        )
