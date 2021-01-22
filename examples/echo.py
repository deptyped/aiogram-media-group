from typing import List

from aiogram import Dispatcher, Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ContentType
from aiogram.utils import executor

from aiogram_media_group import MediaGroupFilter, media_group_handler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(MediaGroupFilter(), content_types=ContentType.PHOTO)
@media_group_handler
async def album_handler(messages: List[types.Message]):
    await messages[-1].reply_media_group(
        [
            types.InputMediaPhoto(
                media=m.photo[-1].file_id,
                caption=m.caption,
                caption_entities=m.caption_entities,
            )
            for m in messages
        ]
    )


if __name__ == "__main__":
    executor.start_polling(dp)
