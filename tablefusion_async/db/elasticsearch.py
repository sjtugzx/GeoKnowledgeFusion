import asyncio
import hashlib
import logging
import pickle

from elasticsearch import AsyncElasticsearch

from tablefusion_async import config
from .redis import redis_set, redis_get

es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.WARNING)

# ==================================================================================================
# Elastic Search


CONNECTION = {}


def get_connection(cluster):
    global CONNECTION
    if cluster not in CONNECTION:
        if cluster not in config.ES_INFO:
            raise Exception(f'No config for the es "{cluster}" found')
        es = AsyncElasticsearch(config.ES_INFO[cluster]['host'])
        es_semaphore = asyncio.Semaphore(config.ES_CONCURRENCY)
        CONNECTION[cluster] = (es, es_semaphore)
    return CONNECTION[cluster]


async def es_search(index: str, body: dict, cluster: str = 'main', cache: bool = False) -> dict:
    if cache:
        md5 = hashlib.md5()
        md5.update(pickle.dumps(body))
        cache_key = f'es_{index}_{md5.hexdigest()}'
        cache = await redis_get(cache_key)
        if cache:
            return cache

    es, es_semaphore = get_connection(cluster)
    if not await es.ping():
        raise Exception('Cannot connect to main Elasticsearch server.')

    async with es_semaphore:
        result = await es.search(index=index, body=body, request_timeout=60)

    if cache:
        await redis_set(cache_key, result)
    return result

# ==================================================================================================
