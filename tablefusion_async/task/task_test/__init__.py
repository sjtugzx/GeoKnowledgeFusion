from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure


@app.task(bind=True, base=BaseTask, queue="table_fusion")
def test_1(self, *args):
    print(f"1 : {args} {self.request.delivery_info['routing_key']}")


@app.task(bind=True, base=BaseTask, queue="table_fusion")
def test_2(self, *args):
    print(f"2 : {args} {self.request.delivery_info['routing_key']}")


@app.task(bind=True, base=BaseTask, queue="test")
def test_3(self, *args):
    print(f"3 : {args} {self.request.delivery_info['routing_key']}")


@app.task(bind=True, base=BaseTask, queue="test")
def test_4(self, *args):
    print(f"4 : {args} {self.request.delivery_info['routing_key']}")
