from functools import lru_cache

from redis.asyncio import Redis

from common.config.settings import get_settings


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


async def is_token_blacklisted(jti: str) -> bool:
    value = await get_redis_client().get(f"jwt:blacklist:{jti}")
    return value == "1"


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    await get_redis_client().setex(f"jwt:blacklist:{jti}", ttl_seconds, "1")

