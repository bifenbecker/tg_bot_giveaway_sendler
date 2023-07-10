import typing
from enum import unique
from tortoise import fields
from tortoise.signals import post_delete, post_save, pre_delete, pre_save
from .db import BaseModel, TimedBaseModel


class GiveAwaySponsor(TimedBaseModel):
    id = fields.IntField(pk=True)
    giveaway = fields.ForeignKeyField('models.GiveAway',
                                      related_name='sponsors', null=False)
    username = fields.CharField(100, null=False)
    chat = fields.ForeignKeyField('models.TelegramChat', related_name='sponsors')
    ok_permissions = fields.BooleanField(default=False, null=False)

    class Meta:
        unique_together = (
            ("chat_id", "giveaway"),
        )