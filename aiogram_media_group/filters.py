from aiogram import types
from aiogram.dispatcher.filters import Filter


class MediaGroupFilter(Filter):
    async def check(self, message: types.Message):
        return message.media_group_id is not None
