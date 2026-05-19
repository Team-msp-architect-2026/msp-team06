import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings

TTL_PRICE = 60 * 60 * 24
TTL_NEWS = 60 * 60 * 2
TTL_MAP = 60 * 60 * 12

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception:
            return None
    return _redis

async def cache_get(key: str) -> Any:
    try:
        redis = await get_redis()
        if not redis:
            return None
        value = await redis.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        return None

async def cache_set(key: str, value: Any, ttl: int = TTL_PRICE) -> None:
    try:
        redis = await get_redis()
        if not redis:
            return
        await redis.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
    except Exception:
        pass