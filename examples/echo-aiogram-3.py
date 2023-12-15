import sys
import logging
from typing import List

from aiogram import Dispatcher, Bot, F, types
from aiogram.types import ContentType

from aiogram_media_group import media_group_handler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(F.media_group_id, F.content_type.in_({'photo'}))
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
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.run_polling(bot)
