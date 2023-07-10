import typing
from enum import unique
from tortoise import fields
from tortoise.signals import post_delete, post_save, pre_delete, pre_save
from .db import BaseModel, TimedBaseModel


class GiveAway(TimedBaseModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, null=False, unique=True)
    author = fields.ForeignKeyField(
        'models.TelegramUser', related_name='giveaways', null=False)
    active = fields.BooleanField(default=True)