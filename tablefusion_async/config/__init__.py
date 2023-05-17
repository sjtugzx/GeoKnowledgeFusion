import datetime
import os
import json

from celery.schedules import crontab
from kombu import Queue, Exchange

# ==================================================================================================
# Project

PROJECT_NAME = 'tablefusion-async'
ENVIRONMENT_PREFIX = PROJECT_NAME.upper().replace('-', '_')

MAJOR_VERSION = 0
MINOR_VERSION = 1
PATCH_VERSION = 0
VERSION = f'{MAJOR_VERSION}.{MINOR_VERSION}.{PATCH_VERSION}'

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

# ==================================================================================================
# Database and search engine configurations

ES_SEARCH_TIMEOUT = '5m'
ES_CONCURRENCY = 100
ES_MAX_SIZE = 0x7fffffff

# ==================================================================================================
# File accessing and file io

# Chunk size while reading files. Large value will cause large memory use, but faster.
CHUNK_SIZE = 1024 * 1024

# UTC bias
TIMEDELTA = datetime.timedelta(hours=8)

PDF_DIR = os.path.join(PROJECT_ROOT, 'static/upload/pdf')
PDF_PROCESS_DIR = os.path.join(PROJECT_ROOT, 'static/processed/pdf')
PDF_XML_DIR = os.path.join(PROJECT_ROOT, 'static/processed/xml')
TABLE_CONTENT_FILE_DIR = os.path.join(PROJECT_ROOT, 'static/processed/table/content')

# Base Urls
IMG_BASE_URL = '/api/v2/img'
# SEARCH_RESULT_BASE_URL = '/api/v1/file/search_result'
# PDF_IMAGE_BASE_URL = '/api/v1/file/pdf_img'
# PDF_PARSE_RESULT_BASE_URL = '/api/v1/file/text_result'

# Email Sending
EMAIL = {
    'noreply': {
        'host': 'smtpdm.aliyun.com',
        'port': 465,
        'user': 'noreply@notice.acemap.info',
        'password': 'AceMap2018',
        'nickname': 'TableFusion',
        'reply_to': 'tablefusion@acemap.cn'
    },
    'newsletter': {
        'host': 'smtpdm.aliyun.com',
        'port': 465,
        'user': 'newsletter@notice.acemap.info',
        'password': 'LVnHONmK986eSYgSJIDD',
        'nickname': 'TableFusion',
        'reply_to': 'tablefusion@acemap.cn'
    },
}

# Access Token

# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 days
NUMBER_OF_SERVICE_CALLS_EXPIRE_SECONDS = 60 * 60 * 24 * 1  # 1 days
ACCESS_TOKEN_SECRET_KEY = "92c384453c76c7396310176588306061d39c19a508b2f41682b26d4087efddbb"
ACCESS_TOKEN_ALGORITHM = "HS256"

CELERY_TIMEZONE = 'Asia/Shanghai'
# CELERYD_PREFETCH_MULTIPLIER = 4  # celery worker每次去redis取任务的数量，默认值就是4
# CELERYD_CONCURRENCY = 20         # 并发的worker数量，也是命令行-c指定的数目  Default: Number of CPU cores.
CELERY_ENABLE_UTC = True
CELERY_TRACK_STARTED = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_ACKS_LATE = True
CELERY_TASK_TRACK_STARTED = True
CELERY_QUEUES = (
    Queue('test', Exchange('test'), routing_key='test', queue_arguments={'x-max-priority': 10}),
)
CELERY_ROUTES = {
    'tasks.task_test.test_1': {'queue': 'test'},
    'tasks.task_test.test_2': {'queue': 'test'},
    'tasks.task_test.test_3': {'queue': 'test'}
}
CELERY_TASK_QUEUE_MAX_PRIORITY = 10
CELERY_TASK_DEFAULT_PRIORITY = 5

# ==================================================================================================
# Different config between dev and prd environment

PROJECT_ENV = os.environ.get(f'PROJECT_ENV', 'LOCAL')

if PROJECT_ENV == 'HK':
    from .hk_prd_config import *
else:
    from .dev_config import *


def update_config(name, new_value):
    if name not in globals():
        return
    old_value = globals()[name]
    if isinstance(old_value, (dict, list)):
        globals()[name] = json.loads(new_value)
    else:
        globals()[name] = type(old_value)(new_value)


for k, v in os.environ.items():
    if k.startswith(ENVIRONMENT_PREFIX):
        update_config(k.lstrip(f'{ENVIRONMENT_PREFIX}_'), v)
