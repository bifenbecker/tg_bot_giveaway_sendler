import typing
from enum import Enum
from tortoise import fields
from tortoise.signals import post_delete, post_save, pre_delete, pre_save
from .db import BaseModel, TimedBaseModel


class Mailing(TimedBaseModel):

    class MStatus(Enum):
        wait = 'wait'
        in_progress = 'in_progress'
        paused = 'paused'
        completed = 'completed'

    id = fields.IntField(pk=True)
    giveaway = fields.ForeignKeyField(
        'models.GiveAway', related_name='mailings', null=True)
    name = fields.CharField(max_length=200, null=True)
    author = fields.ForeignKeyField(
        'models.TelegramUser', related_name='admin_mailings')
    tg_message_id = fields.BigIntField()
    status = fields.CharEnumField(MStatus)
    exclude_members = fields.BooleanField(default=True)

    class Meta:
        unique_together = (
            ('giveaway', 'name'),
        )


class MailingUserListReport(TimedBaseModel):

    class MRStatus(Enum):
        queued = 'queued'
        error = 'error'
        success = 'success'

    id = fields.IntField(pk=True)
    mailing = fields.ForeignKeyField(
        'models.Mailing', related_name='user_list')
    user = fields.ForeignKeyField(
        'models.TelegramUser', related_name='reports')
    status = fields.CharEnumField(MRStatus)
    tg_message_id = fields.BigIntField(null=True)

    class Meta:
        unique_together = (
            ('mailing', 'user'),
        )
