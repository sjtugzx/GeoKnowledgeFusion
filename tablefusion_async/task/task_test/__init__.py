from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure
from celery import current_task


@app.task(bind=True, base=BaseTask)
def test_1(self, paper_id: str, content_id: int = 0):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("1 : ", paper_id)


@app.task(bind=True, base=BaseTask)
def test_2(self, paper_id: str, content_id: int = 0):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("2 : ", paper_id)


@app.task(bind=True, base=BaseTask)
def test_3(self, paper_id: str, content_id: int = 0):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("3 : ", paper_id)


@app.task(bind=True, base=BaseTask)
def test_4(self, paper_id: str, content_id: int = 0):
    queue_name = current_task().request.delivery_info['routing_key']
    print("queue_name : ", queue_name)
    print("4 : ", paper_id)
