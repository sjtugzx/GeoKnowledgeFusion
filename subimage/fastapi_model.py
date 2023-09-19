from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
import base64
from fastapi.middleware.cors import CORSMiddleware
import inference as inf
from PIL import Image
import numpy as np
import cv2
from typing import List
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import matplotlib.pyplot as plt
from io import BytesIO

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
    img_base64: str = None

class response_Item(BaseModel):
    subgraph_res: List[List[float]] = Field(...,example = [1.0, 2.0, 3.0, 4.0])

@app.post('/pic_seg')
async def segmentation(request_data: Item):
    img_base64 = request_data.img_base64
    img_bytes = base64.b64decode(img_base64.encode('utf-8'))
    img = np.array(plt.imread(BytesIO(img_bytes), "PNG"))
    img = Image.fromarray(img[:,:,0])
    subgraph_res = yolo_subgraph.detect_image_fastapi(img)    

    sres = []
    h = img.height
    w = img.width
    for res in subgraph_res:
        tmp = []
        tmp.append(float(res[0])/float(w))
        tmp.append(float(res[1])/float(h))
        tmp.append(float(res[2])/float(w))
        tmp.append(float(res[3])/float(h))
        for i in range(len(tmp)):
            if tmp[i] < 0:
                tmp[i] = 0
            if tmp[i] > 1:
                tmp[i] = 1
        sres.append(tmp)
    # print(sres)
    return sres
    # return [1,2,3,4], [1,2,3,4]

if __name__ == '__main__':
    yolo_subgraph = inf.mAP_Yolo()
    print("Models loaded.")
    uvicorn.run(app=app, host="0.0.0.0", port=12345, workers=1)