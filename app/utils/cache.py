import redis
import os




# app/utils/cache.py




redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))

redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

