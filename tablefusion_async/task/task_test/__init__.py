from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure


@app.task(bind=True, base=BaseTask)
def test_1(self, paper_id: str, content_id: int = 0):
    print("1 : ", paper_id)


@app.task(bind=True, base=BaseTask)
def test_2(self, paper_id: str, content_id: int = 0):
    print("2 : ", paper_id)


@app.task(bind=True, base=BaseTask)
def test_3(self, paper_id: str, content_id: int = 0):
    print("3 : ", paper_id)


@app.task(bind=True, base=BaseTask)
def test_4(self, paper_id: str, content_id: int = 0):
    print("4 : ", paper_id)
