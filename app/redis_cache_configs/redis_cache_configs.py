import redis.asyncio as aioredis

from configs.util_configs import get_settings

settings = get_settings()




async def gemini_redis_cache_keys():
    gemini_redis_cache_keys = await aioredis.from_url(
        settings.REDIS_URL_1,
        decode_responses=True,
    )
    return gemini_redis_cache_keys




