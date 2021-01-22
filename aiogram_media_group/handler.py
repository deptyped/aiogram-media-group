import asyncio
from functools import wraps
from typing import TYPE_CHECKING, Callable, Optional

from aiogram import types, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage as AiogramMemoryStorage
from aiogram.contrib.fsm_storage.redis import (
    RedisStorage as AiogramRedisStorage,
    RedisStorage2 as AiogramRedis2Storage,
)
from aiogram.dispatcher import FSMContext

from aiogram_media_group.storages.base import BaseStorage
from aiogram_media_group.storages.memory import MemoryStorage
from aiogram_media_group.storages.redis import RedisStorage

if TYPE_CHECKING:
    import aioredis


async def _get_storage_from_state(state: FSMContext, prefix, ttl):
    storage_type = type(state.storage)
    if storage_type is AiogramMemoryStorage:
        return MemoryStorage(data=state.storage.data, prefix=prefix)
    elif storage_type is AiogramRedisStorage:
        connection: aioredis.RedisConnection = await state.storage.redis()
        return RedisStorage(connection=connection, prefix=prefix, ttl=ttl)
    elif storage_type is AiogramRedis2Storage:
        redis: aioredis.Redis = await state.storage.redis()
        return RedisStorage(connection=redis.connection, prefix=prefix, ttl=ttl)
    else:
        raise ValueError(f"{storage_type} is unsupported storage")


async def _on_media_group_received(
    media_group_id: str,
    storage: BaseStorage,
    callback,
    *args,
    **kwargs,
):
    messages = await storage.get_media_group_messages(media_group_id)
    await storage.delete_media_group(media_group_id)

    return await callback(messages, *args, **kwargs)


def media_group_handler(
    func: Optional[Callable] = None,
    receive_timeout: float = 1.0,
    storage_prefix: str = "media-group",
    loop=None,
    storage_driver: Optional[BaseStorage] = None,
):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: types.Message, *args, **kwargs):
            if message.media_group_id is None:
                raise ValueError("Not a media group message")

            if loop is None:
                event_loop = asyncio.get_event_loop()
            else:
                event_loop = loop

            if storage_driver is not None:
                storage = storage_driver
            else:
                ttl = int(receive_timeout * 2)
                if ttl < 1:
                    ttl = 1

                state = Dispatcher.get_current().current_state()
                storage = await _get_storage_from_state(
                    state, prefix=storage_prefix, ttl=ttl
                )

            if await storage.set_media_group_as_handled(message.media_group_id):
                event_loop.call_later(
                    receive_timeout,
                    asyncio.create_task,
                    _on_media_group_received(
                        message.media_group_id, storage, handler, *args, **kwargs
                    ),
                )

            await storage.append_message_to_media_group(message.media_group_id, message)

        return wrapper

    if callable(func):
        return decorator(func)

    return decorator
