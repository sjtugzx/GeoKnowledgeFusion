from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
import base64
from fastapi.middleware.cors import CORSMiddleware
import roc_inference as roc_inf
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

@app.post('/label_seg')
async def segmentation(request_data: Item):
    img_base64 = request_data.img_base64
    img_bytes = base64.b64decode(img_base64.encode('utf-8'))
    img = np.array(plt.imread(BytesIO(img_bytes), "PNG"))
    img = Image.fromarray(img[:,:,0])
    word_res = yolo_word.detect_image_fastapi(img)
    dis = 99999999
    flag = 0
    for word in word_res:
        dis1 = ((word[0] + word[2])/2 - img.width)**2 + ((word[1] + word[3])/2 - img.height)**2
        if dis1 < dis:
            dis = dis1
            flag = word_res.index(word)
    wres = word_res[flag]
    h = img.height
    w = img.width
    wres[0] = float(wres[0])/float(w)
    wres[1] = float(wres[1])/float(h)
    wres[2] = float(wres[2])/float(w)
    wres[3] = float(wres[3])/float(h)
    for i in range(len(wres)):
        if wres[i] < 0:
            wres[i] = 0
        if wres[i] > 1:
            wres[i] = 1
    
    return wres

if __name__ == '__main__':
    yolo_word = roc_inf.mAP_Yolo()
    print("Models loaded.")
    uvicorn.run(app=app, host="0.0.0.0", port=12346, workers=1)