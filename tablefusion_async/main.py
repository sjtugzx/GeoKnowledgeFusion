import os
import logging

from celery import Celery

from tablefusion_async import config
from tablefusion_async.common.utils import init_sentry

logger = logging.getLogger(__name__)

init_sentry(config.SENTRY_DSN, config.PROJECT_ENV)

app = Celery(
    config.PROJECT_NAME,
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=[
        'tablefusion_async.task'
    ]
)

app.conf.update(
    CELERY_TASK_SERIALIZER=config.CELERY_TASK_SERIALIZER,
    CELERY_RESULT_SERIALIZER=config.CELERY_RESULT_SERIALIZER,
    CELERY_ACCEPT_CONTENT=config.CELERY_ACCEPT_CONTENT,
    CELERY_TIMEZONE=config.CELERY_TIMEZONE,
    CELERY_ENABLE_UTC=config.CELERY_ENABLE_UTC,
    CELERY_TASK_REJECT_ON_WORKER_LOST=config.CELERY_TASK_REJECT_ON_WORKER_LOST,
    CELERY_ACKS_LATE=config.CELERY_ACKS_LATE,
    CELERY_TASK_TRACK_STARTED=config.CELERY_TASK_TRACK_STARTED,
    CELERY_DEFAULT_PRIORITY=config.CELERY_TASK_DEFAULT_PRIORITY,
    CELERY_QUEUE_MAX_PRIORITY=config.CELERY_TASK_QUEUE_MAX_PRIORITY,
    CELERY_QUEUES=config.CELERY_QUEUES,
    CELERY_ROUTES=config.CELERY_ROUTES
    # CELERYD_CONCURRENCY=config.CELERYD_CONCURRENCY
)

for arg in config.__dict__.keys():
    if arg.endswith('_DIR'):
        os.makedirs(config.__dict__[arg], exist_ok=True)

if __name__ == '__main__':
    app.start()
