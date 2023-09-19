
from typing import List
import uvicorn
from fastapi import FastAPI, File, UploadFile
from starlette.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app = FastAPI(
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    img: UploadFile = File(...)

class response_Item(BaseModel):
    img_path: str = None
    img_name: str = None


@app.post("/file")
async def create_files(file: UploadFile = File(...)):
    name = file.filename
    content = await file.read()
    with open('../fastapi_upload/' + name, 'wb') as f:
        f.write(content)
    img_path = "/home/troykuo/tocr/py37_pytorch/fastapi_upload/" + name
    return img_path, name


# @app.get("/")
# async def main():
#     content = """
# <body>
# <form action="/file/" enctype="multipart/form-data" method="post">
# <input name="file" type="file">
# <input type="submit" value="file上传">
# </body>
#  """
#     return HTMLResponse(content=content)


if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=12348, workers=1)
