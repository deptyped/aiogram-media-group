import asyncio
from functools import wraps
from typing import Callable, Optional

from aiogram import types, Bot, Dispatcher

from aiogram_media_group import AIOGRAM_VERSION
from aiogram_media_group.storages.memory import MemoryStorage
from aiogram_media_group.storages.base import BaseStorage

if AIOGRAM_VERSION == 3:
    # from aiogram.dispatcher.fsm.storage.base import BaseStorage as AiogramBaseStorage
    # from aiogram.dispatcher.fsm.storage.memory import MemoryStorage as AiogramMemoryStorage
    # try:
    #     import aioredis

    #     from aiogram.dispatcher.fsm.storage.redis import RedisStorage as AiogramRedisStorage

    #     from aiogram_media_group.storages.redis import RedisStorage
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

        from aiogram_media_group.storages.redis import RedisStorage
    except ModuleNotFoundError:
        # ignore if aioredis is not installed
        pass
    else:
        REDIS_INSTALLED = True


    async def _wrap_storage(storage: AiogramBaseStorage, prefix, ttl):
        storage_type = type(storage)
        
        if storage_type is AiogramMemoryStorage:
            return MemoryStorage(data=storage.data, prefix=prefix)
        
        elif MONGO_INSTALLED:
            if storage_type is AiogramMongoStorage:
                mongo: motor_asyncio.AsyncIOMotorDatabase = await storage.get_db()
                return await MongoStorage.init(db=mongo)
        
        elif REDIS_INSTALLED:
            if storage_type is AiogramRedisStorage:
                connection: aioredis.RedisConnection = await storage.redis()
                return RedisStorage(connection=connection, prefix=prefix, ttl=ttl)
            elif storage_type is AiogramRedis2Storage:
                redis: aioredis.Redis = await storage.redis()
                return RedisStorage(connection=redis.connection, prefix=prefix, ttl=ttl)
        
        else:
            raise ValueError(f"{storage_type} is unsupported storage")


# to avoid errors and multiple calls to the same function
handled_media_groups = []
EXECUTING_CALLBACK = False


async def _on_media_group_received(
    media_group_id: str,
    storage: BaseStorage,
    callback,
    event_loop,
    unhandle_timeout: float,
    *args,
    **kwargs,
):
    global EXECUTING_CALLBACK

    while EXECUTING_CALLBACK:
        await asyncio.sleep(0)
    else:
        EXECUTING_CALLBACK = True
    
    if not media_group_id in handled_media_groups:
        handled_media_groups.append(media_group_id)
        EXECUTING_CALLBACK = False

        messages = await storage.get_media_group_messages(media_group_id)
        await storage.delete_media_group(media_group_id)

        event_loop.call_later(
            unhandle_timeout,
            asyncio.create_task,
            unhandle_media_group(media_group_id),
        )

        return await callback(messages, *args, **kwargs)
        
    EXECUTING_CALLBACK = False


async def unhandle_media_group(media_group_id: str):
    handled_media_groups.remove(media_group_id)


def media_group_handler(
    func: Optional[Callable] = None,
    only_album: bool = True,
    receive_timeout: float = 1.0,
    storage_prefix: str = "media-group",
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

            if AIOGRAM_VERSION == 3:
                storage = MemoryStorage(STORAGE, prefix='')
            elif AIOGRAM_VERSION == 2:
                storage = await _wrap_storage(
                    Dispatcher.get_current().storage, prefix=storage_prefix, ttl=ttl
                )

            if await storage.set_media_group_as_handled(message.media_group_id):
                event_loop.call_later(
                    receive_timeout,
                    asyncio.create_task,
                    _on_media_group_received(
                        message.media_group_id, storage, handler, event_loop, 2.0, *args, **kwargs
                    ),
                )

            await storage.append_message_to_media_group(message.media_group_id, message)

        return wrapper

    if callable(func):
        return decorator(func)

    return decorator
