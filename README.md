# aiogram-media-group

aiogram handler for media groups (also known as albums)

### Supported drivers

- [In-memory](aiogram_media_group/storages/memory.py)
- [Redis](aiogram_media_group/storages/redis.py) (aiogram 2.x only)
- [Mongo DB](aiogram_media_group/storages/mongo.py) (aiogram 2.x only)

### Install

```bash
pip install aiogram-media-group
# or
poetry add aiogram-media-group
```

### Usage

Minimal usage example:

```python
from aiogram_media_group import media_group_handler

@dp.message(F.media_group_id, F.content_type.in_({'photo'}))
@media_group_handler
async def album_handler(messages: List[types.Message]):
    print(messages)
```

Checkout [examples](https://github.com/deptyped/aiogram-media-group/blob/main/examples) for complete usage examples
