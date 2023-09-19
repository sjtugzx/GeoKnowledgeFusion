import requests
import json
import base64

def test(img_path):
    with open(img_path, 'rb') as f:
        base64_data = base64.b64encode(f.read())
        img = base64_data.decode()
    datas = json.dumps({'img_base64': img})
    rec = requests.post("http://0.0.0.0:12345/pic_seg", data=datas) 
    return rec.text
 
result= test('../fastapi_upload/test.png')
print(result)