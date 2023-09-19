from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
# import base64
from fastapi.middleware.cors import CORSMiddleware
import inference as inf
import roc_inference as roc_inf
import numpy as np
from PIL import Image
import os
import cv2
from typing import List
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import sys
if not "/home/troykuo/tocr/PaddleOCR/tools/" in sys.path:
    sys.path.append("/home/troykuo/tocr/PaddleOCR/tools/")
import test_hubserving_1 as hub

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


# def base64toCV(base64_src):
#     img_b64decode = base64.b64decode(base64_src)  # base64解码
#     img_array = np.fromstring(img_b64decode, np.uint8)  # 转换np序列
#     img_cv = cv2.imdecode(img_array, cv2.COLOR_BGR2RGB)  # 转换OpenCV格式
#     return img_cv

class Item(BaseModel):
    img_path: str = "/home/troykuo/tocr/py37_pytorch/fastapi_upload/test.png"
    img_name: str = "test.png"

class response_Item(BaseModel):
    subgraph_res: List[float] = Field(...,example = [1.0, 2.0, 3.0, 4.0])
    ocr_res: List[str] = Field(...,example = ['1', '2'])

@app.post('/pic_seg')
async def segmentation(request_data: Item):
    img_path = request_data.img_path
    name = request_data.img_name
    img = Image.open(img_path)
    subgraph_res = yolo_subgraph.detect_image_fastapi(img)
    word_res = yolo_word.detect_image_fastapi(img)
    if not os.path.exists('../test_fastapi/' + name[:-4]):
        os.mkdir("../test_fastapi/" + name[:-4])
    i = 0
    for res in word_res:
        img1 = cv2.imread(img_path)
        a = res[1]
        b = res[3]
        c = res[0]
        d = res[2]
        if a < 0:
            a=0
        if c < 0:
            c=0
        crop_image = img1[a:b, c:d]
        cv2.imwrite("../test_fastapi/" + name[:-4] + '/' + str(i) + '.png', crop_image, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])
        i += 1
    server_url = "http://0.0.0.0:8869/predict/ocr_rec"
    ocr_img_res = "../test_fastapi/" + name[:-4] + '/'
    ocr_res = hub.main(server_url, ocr_img_res)
    # print(ocr_res)
    ores = {}
    for key in ocr_res.keys():
        n_index = key.rfind('/')
        new_key = key[n_index+1:]
        ores[int(new_key[:-4])] = ocr_res[key]['results'][0][0]['text']
    # print(ores)
    sub_ores = []
    for res in subgraph_res:
        a = res[1]
        b = res[3]
        c = res[0]
        d = res[2]
        if a < 0:
            a=0
        if c < 0:
            c=0
        cen = (int((d+c)/2), int((b+a)/2))
        dis_center = 99999999
        dis_corner = 99999999
        d_center_index = 0
        d_corner_index = 0
        for ress in word_res:
            aa = ress[1]
            bb = ress[3]
            cc = ress[0]
            dd = ress[2]
            if aa < 0:
                aa=0
            if cc < 0:
                cc=0
            cen1 = (int((dd+cc)/2), int((bb+aa)/2))
            dis1 = ((cen1[0] - cen[0])**2 + (cen1[1] - cen[1])**2)**0.5
            if dis1 < dis_center:
                dis_center = dis1
                d_center_index = word_res.index(ress)
            corners_d = []
            dis2 = ((cen1[0] - c)**2 + (cen1[1] - a)**2)**0.5
            corners_d.append(((cen1[0] - c)**2 + (cen1[1] - b)**2)**0.5)
            corners_d.append(((cen1[0] - d)**2 + (cen1[1] - a)**2)**0.5)
            corners_d.append(((cen1[0] - d)**2 + (cen1[1] - b)**2)**0.5)
            for corner_d in corners_d:
                if corner_d < dis2:
                    dis2 = corner_d
            if dis2 < dis_corner:
                dis_corner = dis2
                d_corner_index = word_res.index(ress)
        if d_center_index != d_corner_index:
            cen_corner = (int((word_res[d_corner_index][2]+word_res[d_corner_index][0])/2), int((word_res[d_corner_index][3]+word_res[d_corner_index][1])/2))
            dis_corner_cen = ((cen_corner[0] - cen[0])**2 + (cen_corner[1] - cen[1])**2)**0.5
            if dis_corner_cen < dis_center:
                sub_ores.append(ores[d_corner_index])
            else:
                sub_ores.append(ores[d_corner_index])
        else:
            sub_ores.append(ores[d_corner_index])
    # print(sub_ores)
    # print(len(sub_ores))

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
        sres.append(tmp)
    # sub_ocrres = []
    # for i in range(len(subgraph_res)):
    #     sub_ocrres.append(ores_sub[i])

    return sres, sub_ores
    # return [1,2,3,4], [1,2,3,4]

if __name__ == '__main__':
    yolo_subgraph = inf.mAP_Yolo()
    yolo_word = roc_inf.mAP_Yolo()
    print("Models loaded.")
    uvicorn.run(app=app, host="0.0.0.0", port=12345, workers=1)
    