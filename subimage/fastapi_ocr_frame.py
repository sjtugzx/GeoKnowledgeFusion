from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import sys
if not "/home/troykuo/tocr/PaddleOCR/tools/" in sys.path:
    sys.path.append("/home/troykuo/tocr/PaddleOCR/tools/")
import test_hubserving_1 as hub
import spaCy as spv2

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
    ocr_img_path: str = None

class response_Item(BaseModel):
    ocr_res: List[str] = Field(...,example = ['a', 'b', 'c', 'd'])

@app.post('/ocr')
async def caption_segmentation(request_data: Item):
    ocr_img_res = request_data.ocr_img_path
    server_url = 'http://0.0.0.0:8869/predict/ocr_rec'
    ocr_res = hub.main(server_url, ocr_img_res)
    res = []
    for key in ocr_res.keys():
        res.append(ocr_res[key]["results"][0][0]["text"])
    ocr_res = spv2.label_sort(res)
    return ocr_res

if __name__ == '__main__':
    print('Paddle OCR model loaded.')
    uvicorn.run(app=app, host="0.0.0.0", port=12347, workers=1)