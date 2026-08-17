import json
from redis.asyncio import Redis
from app.core.config import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)
QUEUE='forgeai:runs'

async def enqueue_run(payload:dict):
    await redis.lpush(QUEUE,json.dumps(payload))

async def next_run(timeout:int=5):
    item=await redis.brpop(QUEUE,timeout=timeout)
    return json.loads(item[1]) if item else None

async def rate_limit(key:str,limit:int,window:int=60)->bool:
    k=f'forgeai:rate:{key}'
    count=await redis.incr(k)
    if count==1: await redis.expire(k,window)
    return count<=limit
