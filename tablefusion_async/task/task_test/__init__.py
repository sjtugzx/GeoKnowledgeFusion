from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure


@app.task(bind=True, base=BaseTask, queue="table_fusion")
def test_1(self, *args):
    print("1 : ", args, self.request)


@app.task(bind=True, base=BaseTask, queue="table_fusion")
def test_2(self, *args):
    print("2 : ", args)
    try:
        print(self.request.delivery_info['routing_key'])
    except Exception as e:
        print("error: ", e)


@app.task(bind=True, base=BaseTask, queue="test")
def test_3(self, *args):
    print("3 : ", args)


@app.task(bind=True, base=BaseTask, queue="test")
def test_4(self, *args):
    print("4 : ", args)
