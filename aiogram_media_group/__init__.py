__version__ = "0.5.0"

from aiogram import __version__ as AIOGRAM_VERSION

AIOGRAM_VERSION = int(AIOGRAM_VERSION[0])

if  AIOGRAM_VERSION == 3:
    from aiogram import F
    
    MediaGroupFilter = lambda: F.media_group_id
elif AIOGRAM_VERSION == 2:
    from aiogram.dispatcher.filters import MediaGroupFilter as AiogramMediaGroupFilter
    
    MediaGroupFilter = lambda: AiogramMediaGroupFilter(is_media_group=True)

from .handler import media_group_handler
from . import storages
