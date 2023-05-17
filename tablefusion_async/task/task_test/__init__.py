from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure
from celery import current_task


@app.task(bind=True, base=BaseTask)
def test_1(self, *args):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("1 : ", args)


@app.task(bind=True, base=BaseTask)
def test_2(self, *args):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("2 : ", args)


@app.task(bind=True, base=BaseTask)
def test_3(self, *args):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("3 : ", args)


@app.task(bind=True, base=BaseTask)
def test_4(self, *args):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("4 : ", args)
