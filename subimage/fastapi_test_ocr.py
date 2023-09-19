import requests
import json

def test(img_path):
    datas = json.dumps({'ocr_img_path': img_path})
    rec = requests.post("http://0.0.0.0:12347/ocr", data=datas) 
    return rec.text
 
result= test('../test_fastapi/12/')
print(result)