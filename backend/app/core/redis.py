import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings
import redis as sync_redis
from app.metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL

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

def _cache_type(key: str) -> str:
    """키 프리픽스로 캐시 유형을 추출한다 (price / news / report / other)."""
    prefix = key.split(":")[0] if ":" in key else key
    return prefix if prefix in ("price", "news", "report", "kapt") else "other"


async def cache_get(key: str) -> Any:
    try:
        redis = await get_redis()
        if not redis:
            return None
        value = await redis.get(key)
        cache_type = _cache_type(key)
        if value:
            CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()
            return json.loads(value)
        CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()
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

_sync_redis = None

def get_sync_redis():
    global _sync_redis
    if _sync_redis is None:
        try:
            _sync_redis = sync_redis.from_url(
                "redis://homelens-dev-redis.duvrv2.ng.0001.euw3.cache.amazonaws.com:6379",
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception:
            return None
    return _sync_redis

def report_set(report_id: str, data: dict, ttl: int = 60 * 60 * 2) -> None:
    try:
        r = get_sync_redis()
        if r:
            r.set(f"report:{report_id}", json.dumps(data, ensure_ascii=False), ex=ttl)
    except Exception as e:
        print(f"Redis report_set 실패: {e}")

def report_get(report_id: str) -> dict:
    try:
        r = get_sync_redis()
        if r:
            value = r.get(f"report:{report_id}")
            if value:
                return json.loads(value)
    except Exception as e:
        print(f"Redis report_get 실패: {e}")
    return None