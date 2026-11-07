import logging
import threading
import time
from collections import defaultdict

import redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Atomic Redis token bucket. All API instances share the same bucket per client IP.
_TOKEN_BUCKET_LUA = """
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local server_time = redis.call('TIME')
local now = tonumber(server_time[1]) + tonumber(server_time[2]) / 1000000
local values = redis.call('HMGET', KEYS[1], 'tokens', 'updated_at')
local tokens = tonumber(values[1])
local updated_at = tonumber(values[2])
if tokens == nil then
  tokens = capacity
  updated_at = now
end
local elapsed = math.max(0, now - updated_at)
tokens = math.min(capacity, tokens + elapsed * refill_rate)
local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'updated_at', now)
redis.call('EXPIRE', KEYS[1], math.ceil((capacity / refill_rate) * 2))
return {allowed, math.floor(tokens)}
"""

_redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
_local_lock = threading.Lock()
_local_buckets: dict[str, tuple[float, float]] = defaultdict(lambda: (float(settings.RATE_LIMIT_CAPACITY), time.monotonic()))


def allow_request(client_ip: str) -> bool:
    if not settings.RATE_LIMIT_ENABLED:
        return True
    key = f"linkpulse:rate:{client_ip}"
    try:
        result = _redis.eval(
            _TOKEN_BUCKET_LUA,
            1,
            key,
            settings.RATE_LIMIT_CAPACITY,
            settings.RATE_LIMIT_REFILL_PER_SECOND,
        )
        return bool(int(result[0]))
    except RedisError:
        if not settings.RATE_LIMIT_FAIL_OPEN:
            raise
        # Local fallback keeps development usable; use Redis in production for cross-instance limits.
        logger.warning("Redis rate limiter unavailable; using process-local fallback")
        now = time.monotonic()
        with _local_lock:
            tokens, updated = _local_buckets[key]
            tokens = min(
                float(settings.RATE_LIMIT_CAPACITY),
                tokens + max(0.0, now - updated) * settings.RATE_LIMIT_REFILL_PER_SECOND,
            )
            allowed = tokens >= 1.0
            if allowed:
                tokens -= 1.0
            _local_buckets[key] = (tokens, now)
            return allowed
