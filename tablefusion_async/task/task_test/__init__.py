from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure
from celery import current_task


@app.task(bind=True, base=BaseTask, queue="test")
def test_1(self, *args):
    print("1 : ", args)


@app.task(bind=True, base=BaseTask, queue="test")
def test_2(self, *args):
    print("2 : ", args)


@app.task(bind=True, base=BaseTask, queue="test")
def test_3(self, *args):
    print("3 : ", args)


@app.task(bind=True, base=BaseTask, queue="test")
def test_4(self, *args):
    print("4 : ", args)
