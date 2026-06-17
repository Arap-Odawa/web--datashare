import asyncio
from  google import genai

import time
from datetime import datetime, timezone
from typing import List, Optional
import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from configs.util_configs import get_settings

settings = get_settings()

"""
    The Gemini Connection settings below are used to route llm requests to Gemini while 
    rotating the API keys depending on how the requests and tokens are used depending on 
    the tokens per minute or day or requests per minute or day as set by the llm providers.

    These are divided into paid or free depending on whether it is free or paid 
    or pro vs fast for the thinking depth.
    
    19042026.

"""

# --- The Connection Manager ---
class GeminiFastRotatingAPIKeyManagerSyncSingleRateLimitNotUsed:
    def __init__(self, api_keys: list[str], max_requests: int = 45):
        self.api_keys = settings.gemini_api_keys
        self.current_key_idx = 0  # Starts at the first key
        self.max_requests = max_requests
        self.request_count = 0
        self.client = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initial connection setup using the first key."""
        initial_key = self.api_keys[self.current_key_idx]
        #self.client = await genai.AsyncClient(api_key=initial_key)
        self.client = genai.Client(api_key=initial_key)

    async def get_connection(self):
        """Returns the current connection, rotating keys if necessary."""
        async with self._lock:
            if self.request_count >= self.max_requests:
                await self._rotate()
            
            self.request_count += 1
            return self.client

    async def _rotate(self):
        """Cycles to the next API key and establishes a new connection."""
        print("Limit reached. Rotating API key and database connection...")
        old_client = self.client
        
        # 1. Move to the next key (Loops back to 0 after the 4th key)
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_idx]
        
        # 2. Establish the new connection first
        self.client = genai.Client(api_key=new_key)
        
        # 3. Reset the request counter
        self.request_count = 0
        
        # 4. Clean up the exhausted connection
        if old_client:
            old_client.close

    async def close(self):
        if self.client:
            self.client.close






class GeminiFreeFastRedisRotatingAPIKeyManagerSync:
    def __init__(
        self, 
        #request:Optional[Request],
        redis_url: str=settings.REDIS_URL_1,
        api_keys: List[str] = settings.gemini_api_keys, 
        rpm_limit: int = int(settings.GEMINI_FREE_3_FAST_RATELIMITS_RPM), 
        rpd_limit: int = int(settings.GEMINI_FREE_3_FAST_RATELIMITS_RPD), 
        tpd_limit: int = int(settings.GEMINI_FREE_3_FAST_RATELIMITS_TPM)*int(settings.DAILY_MINUTES),

    ):
        # Create an async Redis connection pool
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        #self.redis=asyncio.create_task(gemini_free_fast_api_manager_1(request=request))
        self.api_keys = api_keys
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.tpd_limit = tpd_limit
        
        self.current_idx = 0
        self.conn = None
        
        # We still use an asyncio lock to prevent the *current worker* # from spamming Redis with rotation requests simultaneously.
        self._lock = asyncio.Lock()

    def _get_redis_keys(self, api_key: str):
        """Generates time-bucketed Redis keys for the current minute and day."""
        now = datetime.now(timezone.utc)
        minute_str = now.strftime("%Y-%m-%dT%H:%M") # e.g., 2026-03-26T10:21
        day_str = now.strftime("%Y-%m-%d")          # e.g., 2026-03-26
        
        # We hash or slice the key for security/brevity in Redis
        safe_key = api_key[-6:] 
        
        return {
            "rpm": f"rate:rpm:{safe_key}:{minute_str}",
            "rpd": f"rate:rpd:{safe_key}:{day_str}",
            "tpd": f"rate:tpd:{safe_key}:{day_str}"
        }

    async def initialize(self):
        initial_key = self.api_keys[self.current_idx]
        #self.conn = await connect_to_database(initial_key)
        self.conn =  genai.Client(api_key=initial_key)
        return self.conn

    async def get_connection(self, expected_tokens: int = 0):
        async with self._lock:
            for _ in range(len(self.api_keys)):
                current_key = self.api_keys[self.current_idx]
                r_keys = self._get_redis_keys(current_key)
                
                # 1. Fetch current usage across all 3 limits simultaneously
                pipe = self.redis.pipeline()
                pipe.get(r_keys["rpm"])
                pipe.get(r_keys["rpd"])
                pipe.get(r_keys["tpd"])
                rpm_val, rpd_val, tpd_val = await pipe.execute()
                
                # Convert Redis string responses to integers (defaulting to 0)
                current_rpm = int(rpm_val or 0)
                current_rpd = int(rpd_val or 0)
                current_tpd = int(tpd_val or 0)
                
                # 2. Evaluate against limits
                if (current_rpm < self.rpm_limit and 
                    current_rpd < self.rpd_limit and 
                    (current_tpd + expected_tokens) <= self.tpd_limit):
                    
                    # 3. Valid! Increment usage in Redis
                    pipe = self.redis.pipeline()
                    pipe.incr(r_keys["rpm"])
                    pipe.incr(r_keys["rpd"])
                    pipe.incrby(r_keys["tpd"], expected_tokens)
                    
                    # Optional: Set a 24h expiration so Redis doesn't fill up with old keys
                    pipe.expire(r_keys["rpm"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["rpd"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["tpd"], int(settings.DAILY_MINUTES))
                    
                    await pipe.execute()
                    
                    return self.conn
                
                # If limits exceeded, rotate and try the next key
                await self._rotate()

            raise HTTPException(
                status_code=429, 
                detail="Rate limits exhausted across all available API keys. Try again later."
            )

    async def _rotate(self):
        print(f"Worker hit limits on key index {self.current_idx}. Rotating...")
        old_conn = self.conn
        
        self.current_idx = (self.current_idx + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_idx]
        
        #self.conn = await connect_to_database(new_key)
        self.conn = await genai.Client(api_key=new_key)
        if old_conn:
            #await close_connection_to_database(old_conn)
            await old_conn.close

    async def record_actual_tokens(self, tokens_used: int):
        """Retroactively updates the token count in Redis."""
        current_key = self.api_keys[self.current_idx]
        r_keys = self._get_redis_keys(current_key)
        await self.redis.incrby(r_keys["tpd"], tokens_used)

    async def close(self):
        if self.conn:
            #await close_connection_to_database(self.conn)
            await self.conn.close
        await self.redis.aclose() # Close the Redis connection pool






class GeminiFreeProRedisRotatingAPIKeyManagerSync:
    def __init__(
        self, 
        #request:Optional[Request],
        redis_url: str=settings.REDIS_URL_1,
        api_keys: List[str] = settings.gemini_api_keys, 
        rpm_limit: int = int(settings.GEMINI_FREE_3_PRO_RATELIMITS_RPM), 
        rpd_limit: int = int(settings.GEMINI_FREE_3_PRO_RATELIMITS_RPD), 
        tpd_limit: int = int(settings.GEMINI_FREE_3_PRO_RATELIMITS_TPM)*int(settings.DAILY_MINUTES),

    ):
        # Create an async Redis connection pool
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        #self.redis = asyncio.create_task(gemini_free_pro_api_manager_1(request=request))
        self.api_keys = api_keys
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.tpd_limit = tpd_limit
        
        self.current_idx = 0
        self.conn = None
        
        # We still use an asyncio lock to prevent the *current worker* # from spamming Redis with rotation requests simultaneously.
        self._lock = asyncio.Lock()

    def _get_redis_keys(self, api_key: str):
        """Generates time-bucketed Redis keys for the current minute and day."""
        now = datetime.now(timezone.utc)
        minute_str = now.strftime("%Y-%m-%dT%H:%M") # e.g., 2026-03-26T10:21
        day_str = now.strftime("%Y-%m-%d")          # e.g., 2026-03-26
        
        # We hash or slice the key for security/brevity in Redis
        safe_key = api_key[-6:] 
        
        return {
            "rpm": f"rate:rpm:{safe_key}:{minute_str}",
            "rpd": f"rate:rpd:{safe_key}:{day_str}",
            "tpd": f"rate:tpd:{safe_key}:{day_str}"
        }

    async def initialize(self):
        initial_key = self.api_keys[self.current_idx]
        #self.conn = await connect_to_database(initial_key)
        self.conn =  genai.Client(api_key=initial_key)
        return self.conn

    async def get_connection(self, expected_tokens: int = 0):
        async with self._lock:
            for _ in range(len(self.api_keys)):
                current_key = self.api_keys[self.current_idx]
                r_keys = self._get_redis_keys(current_key)
                
                # 1. Fetch current usage across all 3 limits simultaneously
                pipe = self.redis.pipeline()
                pipe.get(r_keys["rpm"])
                pipe.get(r_keys["rpd"])
                pipe.get(r_keys["tpd"])
                rpm_val, rpd_val, tpd_val = await pipe.execute()
                
                # Convert Redis string responses to integers (defaulting to 0)
                current_rpm = int(rpm_val or 0)
                current_rpd = int(rpd_val or 0)
                current_tpd = int(tpd_val or 0)
                
                # 2. Evaluate against limits
                if (current_rpm < self.rpm_limit and 
                    current_rpd < self.rpd_limit and 
                    (current_tpd + expected_tokens) <= self.tpd_limit):
                    
                    # 3. Valid! Increment usage in Redis
                    pipe = self.redis.pipeline()
                    pipe.incr(r_keys["rpm"])
                    pipe.incr(r_keys["rpd"])
                    pipe.incrby(r_keys["tpd"], expected_tokens)
                    
                    # Optional: Set a 24h expiration so Redis doesn't fill up with old keys
                    pipe.expire(r_keys["rpm"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["rpd"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["tpd"], int(settings.DAILY_MINUTES))
                    
                    await pipe.execute()
                    
                    return self.conn
                
                # If limits exceeded, rotate and try the next key
                await self._rotate()

            raise HTTPException(
                status_code=429, 
                detail="Rate limits exhausted across all available API keys. Try again later."
            )

    async def _rotate(self):
        print(f"Worker hit limits on key index {self.current_idx}. Rotating...")
        old_conn = self.conn
        
        self.current_idx = (self.current_idx + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_idx]
        
        #self.conn = await connect_to_database(new_key)
        self.conn = await genai.Client(api_key=new_key)
        if old_conn:
            #await close_connection_to_database(old_conn)
            await old_conn.close

    async def record_actual_tokens(self, tokens_used: int):
        """Retroactively updates the token count in Redis."""
        current_key = self.api_keys[self.current_idx]
        r_keys = self._get_redis_keys(current_key)
        await self.redis.incrby(r_keys["tpd"], tokens_used)

    async def close(self):
        if self.conn:
            #await close_connection_to_database(self.conn)
            await self.conn.close
        await self.redis.aclose() # Close the Redis connection pool








class GeminiPaidFastRedisRotatingAPIKeyManagerSync:
    def __init__(
        self, 
        #request:Optional[Request],
        redis_url: str=settings.REDIS_URL_1,
        api_keys: List[str] = settings.gemini_paid_api_keys, 
        rpm_limit: int = int(settings.GEMINI_PAID_3_FAST_RATELIMITS_RPM), 
        rpd_limit: int = int(settings.GEMINI_PAID_3_FAST_RATELIMITS_RPD), 
        tpd_limit: int = int(settings.GEMINI_PAID_3_FAST_RATELIMITS_TPM)*int(settings.DAILY_MINUTES),

    ):
        # Create an async Redis connection pool
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        #self.redis = asyncio.create_task(gemini_paid_fast_api_manager_1(request=request))
        self.api_keys = api_keys
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.tpd_limit = tpd_limit
        
        self.current_idx = 0
        self.conn = None
        
        # We still use an asyncio lock to prevent the *current worker* # from spamming Redis with rotation requests simultaneously.
        self._lock = asyncio.Lock()

    def _get_redis_keys(self, api_key: str):
        """Generates time-bucketed Redis keys for the current minute and day."""
        now = datetime.now(timezone.utc)
        minute_str = now.strftime("%Y-%m-%dT%H:%M") # e.g., 2026-03-26T10:21
        day_str = now.strftime("%Y-%m-%d")          # e.g., 2026-03-26
        
        # We hash or slice the key for security/brevity in Redis
        safe_key = api_key[-6:] 
        
        return {
            "rpm": f"rate:rpm:{safe_key}:{minute_str}",
            "rpd": f"rate:rpd:{safe_key}:{day_str}",
            "tpd": f"rate:tpd:{safe_key}:{day_str}"
        }

    async def initialize(self):
        initial_key = self.api_keys[self.current_idx]
        #self.conn = await connect_to_database(initial_key)
        self.conn =  genai.Client(api_key=initial_key)
        return self.conn

    async def get_connection(self, expected_tokens: int = 0):
        async with self._lock:
            for _ in range(len(self.api_keys)):
                current_key = self.api_keys[self.current_idx]
                r_keys = self._get_redis_keys(current_key)
                
                # 1. Fetch current usage across all 3 limits simultaneously
                pipe = self.redis.pipeline()
                pipe.get(r_keys["rpm"])
                pipe.get(r_keys["rpd"])
                pipe.get(r_keys["tpd"])
                rpm_val, rpd_val, tpd_val = await pipe.execute()
                
                # Convert Redis string responses to integers (defaulting to 0)
                current_rpm = int(rpm_val or 0)
                current_rpd = int(rpd_val or 0)
                current_tpd = int(tpd_val or 0)
                
                # 2. Evaluate against limits
                if (current_rpm < self.rpm_limit and 
                    current_rpd < self.rpd_limit and 
                    (current_tpd + expected_tokens) <= self.tpd_limit):
                    
                    # 3. Valid! Increment usage in Redis
                    pipe = self.redis.pipeline()
                    pipe.incr(r_keys["rpm"])
                    pipe.incr(r_keys["rpd"])
                    pipe.incrby(r_keys["tpd"], expected_tokens)
                    
                    # Optional: Set a 24h expiration so Redis doesn't fill up with old keys
                    pipe.expire(r_keys["rpm"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["rpd"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["tpd"], int(settings.DAILY_MINUTES))
                    
                    await pipe.execute()
                    
                    return self.conn
                
                # If limits exceeded, rotate and try the next key
                await self._rotate()

            raise HTTPException(
                status_code=429, 
                detail="Rate limits exhausted across all available API keys. Try again later."
            )

    async def _rotate(self):
        print(f"Worker hit limits on key index {self.current_idx}. Rotating...")
        old_conn = self.conn
        
        self.current_idx = (self.current_idx + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_idx]
        
        #self.conn = await connect_to_database(new_key)
        self.conn = await genai.Client(api_key=new_key)
        if old_conn:
            #await close_connection_to_database(old_conn)
            await old_conn.close

    async def record_actual_tokens(self, tokens_used: int):
        """Retroactively updates the token count in Redis."""
        current_key = self.api_keys[self.current_idx]
        r_keys = self._get_redis_keys(current_key)
        await self.redis.incrby(r_keys["tpd"], tokens_used)

    async def close(self):
        if self.conn:
            #await close_connection_to_database(self.conn)
            await self.conn.close
        await self.redis.aclose() # Close the Redis connection pool






class GeminiPaidProRedisRotatingAPIKeyManagerSync:
    def __init__(
        self, 
        #request:Optional[Request],
        redis_url: str=settings.REDIS_URL_1,
        api_keys: List[str] = settings.gemini_paid_api_keys, 
        rpm_limit: int = int(settings.GEMINI_PAID_3_PRO_RATELIMITS_RPM), 
        rpd_limit: int = int(settings.GEMINI_PAID_3_PRO_RATELIMITS_RPD), 
        tpd_limit: int = int(settings.GEMINI_PAID_3_PRO_RATELIMITS_TPM)*int(settings.DAILY_MINUTES),

    ):
        # Create an async Redis connection pool
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        #self.redis = asyncio.create_task(gemini_paid_pro_api_manager_1(request=request))
        self.api_keys = api_keys
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.tpd_limit = tpd_limit
        
        self.current_idx = 0
        self.conn = None
        
        # We still use an asyncio lock to prevent the *current worker* # from spamming Redis with rotation requests simultaneously.
        self._lock = asyncio.Lock()

    def _get_redis_keys(self, api_key: str):
        """Generates time-bucketed Redis keys for the current minute and day."""
        now = datetime.now(timezone.utc)
        minute_str = now.strftime("%Y-%m-%dT%H:%M") # e.g., 2026-03-26T10:21
        day_str = now.strftime("%Y-%m-%d")          # e.g., 2026-03-26
        
        # We hash or slice the key for security/brevity in Redis
        safe_key = api_key[-6:] 
        
        return {
            "rpm": f"rate:rpm:{safe_key}:{minute_str}",
            "rpd": f"rate:rpd:{safe_key}:{day_str}",
            "tpd": f"rate:tpd:{safe_key}:{day_str}"
        }

    async def initialize(self):
        initial_key = self.api_keys[self.current_idx]
        #self.conn = await connect_to_database(initial_key)
        self.conn =  genai.Client(api_key=initial_key)
        return self.conn

    async def get_connection(self, expected_tokens: int = 0):
        async with self._lock:
            for _ in range(len(self.api_keys)):
                current_key = self.api_keys[self.current_idx]
                r_keys = self._get_redis_keys(current_key)
                
                # 1. Fetch current usage across all 3 limits simultaneously
                pipe = self.redis.pipeline()
                pipe.get(r_keys["rpm"])
                pipe.get(r_keys["rpd"])
                pipe.get(r_keys["tpd"])
                rpm_val, rpd_val, tpd_val = await pipe.execute()
                
                # Convert Redis string responses to integers (defaulting to 0)
                current_rpm = int(rpm_val or 0)
                current_rpd = int(rpd_val or 0)
                current_tpd = int(tpd_val or 0)
                
                # 2. Evaluate against limits
                if (current_rpm < self.rpm_limit and 
                    current_rpd < self.rpd_limit and 
                    (current_tpd + expected_tokens) <= self.tpd_limit):
                    
                    # 3. Valid! Increment usage in Redis
                    pipe = self.redis.pipeline()
                    pipe.incr(r_keys["rpm"])
                    pipe.incr(r_keys["rpd"])
                    pipe.incrby(r_keys["tpd"], expected_tokens)
                    
                    # Optional: Set a 24h expiration so Redis doesn't fill up with old keys
                    pipe.expire(r_keys["rpm"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["rpd"], int(settings.DAILY_MINUTES))
                    pipe.expire(r_keys["tpd"], int(settings.DAILY_MINUTES))
                    
                    await pipe.execute()
                    
                    return self.conn
                
                # If limits exceeded, rotate and try the next key
                await self._rotate()

            raise HTTPException(
                status_code=429, 
                detail="Rate limits exhausted across all available API keys. Try again later."
            )

    async def _rotate(self):
        print(f"Worker hit limits on key index {self.current_idx}. Rotating...")
        old_conn = self.conn
        
        self.current_idx = (self.current_idx + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_idx]
        
        #self.conn = await connect_to_database(new_key)
        self.conn = await genai.Client(api_key=new_key)
        if old_conn:
            #await close_connection_to_database(old_conn)
            await old_conn.close

    async def record_actual_tokens(self, tokens_used: int):
        """Retroactively updates the token count in Redis."""
        current_key = self.api_keys[self.current_idx]
        r_keys = self._get_redis_keys(current_key)
        await self.redis.incrby(r_keys["tpd"], tokens_used)

    async def close(self):
        if self.conn:
            #await close_connection_to_database(self.conn)
            await self.conn.close
        await self.redis.aclose() # Close the Redis connection pool































