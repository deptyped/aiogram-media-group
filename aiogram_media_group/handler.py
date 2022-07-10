import asyncio
from functools import wraps
from typing import Callable, Optional

from aiogram import types, Bot, Dispatcher

from . import AIOGRAM_VERSION
from .storages.memory import MemoryStorage
from .storages.base import BaseStorage

if AIOGRAM_VERSION == 3:
    # Currently for aiogram3 MemoryStorage is used, because this version is still in development
    # It breaks backward compatibility by introducing new breaking changes

    # from aiogram.dispatcher.fsm.storage.base import BaseStorage as AiogramBaseStorage
    # from aiogram.dispatcher.fsm.storage.memory import MemoryStorage as AiogramMemoryStorage
    # try:
    #     import aioredis

    #     from aiogram.dispatcher.fsm.storage.redis import RedisStorage as AiogramRedisStorage

    #     from .storages.redis import RedisStorage
    # except ModuleNotFoundError:
    #     # ignore if aioredis is not installed
    #     pass

    STORAGE = {}

elif AIOGRAM_VERSION == 2:
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.storage import BaseStorage as AiogramBaseStorage
    from aiogram.contrib.fsm_storage.memory import MemoryStorage as AiogramMemoryStorage

    MONGO_INSTALLED = False
    REDIS_INSTALLED = False

    try:
        from motor import motor_asyncio

        from aiogram.contrib.fsm_storage.mongo import MongoStorage as AiogramMongoStorage

        from .storages.mongo import MongoStorage
    except ModuleNotFoundError:
        # ignore if motor is not installed
        pass
    else:
        MONGO_INSTALLED = True
    

    try:
        import aioredis

        from aiogram.contrib.fsm_storage.redis import (
            RedisStorage as AiogramRedisStorage,
            RedisStorage2 as AiogramRedis2Storage,
        )

        from .storages.redis import RedisStorage
    except ModuleNotFoundError:
        # ignore if aioredis is not installed
        pass
    else:
        REDIS_INSTALLED = True


    async def _wrap_storage(storage: AiogramBaseStorage, prefix: str, ttl: int):
        storage_type = type(storage)
        
        if storage_type is AiogramMemoryStorage:
            return MemoryStorage(data=storage.data, prefix=prefix)
        
        elif MONGO_INSTALLED:
            if storage_type is AiogramMongoStorage:
                mongo: motor_asyncio.AsyncIOMotorDatabase = await storage.get_db()
                return MongoStorage(db=mongo, prefix=prefix, ttl=ttl)
        
        elif REDIS_INSTALLED:
            if storage_type is AiogramRedisStorage:
                connection: aioredis.RedisConnection = await storage.redis()
                return RedisStorage(connection=connection, prefix=prefix, ttl=ttl)
            elif storage_type is AiogramRedis2Storage:
                redis: aioredis.Redis = await storage.redis()
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
    only_album: bool = True,
    receive_timeout: float = 1.0,
    storage_prefix: str = "aiogram_media_group",
    storage_driver: BaseStorage=None,
    loop=None
):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: types.Message, *args, **kwargs):

            if only_album and message.media_group_id is None:
                raise ValueError("Not a media group message")
            elif message.media_group_id is None:
                return await handler([message], *args, **kwargs)

            event_loop = asyncio.get_running_loop() if loop is None else loop

            ttl = int(receive_timeout * 2)
            if ttl < 1:
                ttl = 1
            
            if storage_driver:
                storage = storage_driver
            else:
                if AIOGRAM_VERSION == 3:
                    storage = MemoryStorage(STORAGE, prefix='')
                elif AIOGRAM_VERSION == 2:
                    storage = await _wrap_storage(
                        Dispatcher.get_current().storage, storage_prefix, ttl
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
