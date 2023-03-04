import pickle

import aioredis

from tablefusion_async import config

POOL = {}


async def get_pool(db) -> aioredis.commands.Redis:
    global POOL
    if db not in POOL:
        POOL[db] = await aioredis.create_redis_pool(
            maxsize=20,
            address=config.REDIS_INFO[db]['address'],
            db=config.REDIS_INFO[db]['db'],
            password=config.REDIS_INFO[db].get('password', None),
        )
    return POOL[db]


async def redis_set(key, value, db='main', expire=None) -> bool:
    if expire is None:
        expire = config.REDIS_INFO[db]['expire']
    value_bytes = pickle.dumps(value)
    pool = await get_pool(db)
    try:
        result = await pool.set(key, value_bytes, expire=expire)
        return result
    except aioredis.RedisError:
        return False


async def redis_get(key, db='main'):
    pool = await get_pool(db)
    try:
        value_bytes = await pool.get(key)
        if value_bytes:
            return pickle.loads(value_bytes)
        else:
            return None
    except aioredis.RedisError:
        return None


async def redis_delete(key, db='main') -> int:
    pool = await get_pool(db)
    try:
        if isinstance(key, list):
            result = await pool.delete(*key)
        else:
            result = await pool.delete(key)
        return result
    except aioredis.RedisError:
        return 0


async def redis_refresh(key, db='main', expire=None) -> bool:
    if expire is None:
        expire = config.REDIS_INFO[db]['expire']
    pool = await get_pool(db)
    try:
        result = await pool.expire(key, expire)
        return result
    except aioredis.RedisError:
        return False
