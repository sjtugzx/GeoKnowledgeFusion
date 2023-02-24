import logging

from celery import Task


logger = logging.getLogger(__name__)


class BaseTask(Task):
    def run(self, *args, **kwargs):
        """The body of the task executed by workers."""
        raise NotImplementedError('Tasks must define the run method.')

    def before_start(self, task_id, args, kwargs):
        logger.info(f'开始执行task，task id为:{task_id} args: {args} kwargs: {kwargs}')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.info(f'执行task失败，task id为:{task_id} args: {args} kwargs: {kwargs}')

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f'执行task成功，task id为:{task_id} args: {args} kwargs: {kwargs}')


class TaskFailure(Exception):
    pass
