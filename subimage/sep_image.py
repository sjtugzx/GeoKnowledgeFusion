import inference as inf
import roc_inference as roc_inf
import json
import sys
import io
import os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
from PIL import Image
import cv2
import string
import re
import spacy
import scispacy
import spaCy as spcv2
if not "/home/troykuo/ocr/PaddleOCR/tools/" in sys.path:
    sys.path.append("/home/troykuo/tocr/PaddleOCR/tools/")

import infer_rec1 as infer_rec
import time

time_start = time.time()

def image_information_extraction(file_path):
    with open(file_path + '/figure-data.json', 'r', encoding='utf8') as fp:
        json_data = json.load(fp)
    res = {}
    for i in json_data:
        if i['figType'] == 'Figure':
            res[i['renderURL'][:-4]] = i['caption']
    return res

spcv2.load_Abbreviations("Abbreviations.txt")
#nlp1 = spacy.load("en_core_sci_lg")
nlp1 = spacy.load("en_core_sci_sm")
print(1)
file_path = 'Chen et al 2006 Episodes.pdffigures2.figure'
info = image_information_extraction('../input/' + file_path)
yolo_subgraph = inf.mAP_Yolo()
yolo_word = roc_inf.mAP_Yolo()
image_ids = info.keys()

if not os.path.exists("../output"):
    os.makedirs("../output")
if not os.path.exists("../output/detection-results"):
    os.makedirs("../output/detection-results")
    os.makedirs("../output/detection-results/" + file_path)
if not os.path.exists("../output/images-optional"):
    os.makedirs("../output/images-optional")
    os.makedirs("../output/images-optional/" + file_path)
if not os.path.exists("../output/caption"):
    os.makedirs("../output/caption")
    os.makedirs("../output/caption/" + file_path)


if not os.path.exists("../output_word"):
    os.makedirs("../output_word")
if not os.path.exists("../output_word/detection-results"):
    os.makedirs("../output_word/detection-results")
    os.makedirs("../output_word/detection-results/" + file_path)
if not os.path.exists("../output_word/images-optional"):
    os.makedirs("../output_word/images-optional")
    os.makedirs("../output_word/images-optional/" + file_path)
if not os.path.exists("../output_word/caption"):
    os.makedirs("../output_word/caption")
    os.makedirs("../output_word/caption/" + file_path)

for image_id in image_ids:
    image_path = "../input/" + file_path + '/' + image_id
    image = Image.open(image_path + '.png')
    yolo_subgraph.detect_image(file_path + '/' + image_id, image)
    yolo_word.detect_image(file_path + '/' + image_id, image)
    image.save("../output/images-optional/"+ file_path + '/' + image_id+".png")
    image.save("../output_word/images-optional/"+ file_path + '/' + image_id+".png")
    print(file_path + '/' + image_id," done!")

detection_results_path_subgraph="../output/detection-results" + '/' + file_path
images_path_subgraph="../output/images-optional" + '/' + file_path
detection_results = os.listdir(detection_results_path_subgraph)
right_bottom = []
for detection_result in detection_results: 
    # print(detection_result)
    image_name = detection_result.split('.')[0]
    image =  images_path_subgraph+ '/' + image_name+'.png'
    # print(image)
    f = open(detection_results_path_subgraph + '/' + detection_result, "r")
    lines = f.readlines()
    num=1
    for line in lines:
        l = line.split(' ')
        tmp = []
        tmp.append(l[4])
        tmp.append(l[5])
        right_bottom.append(tmp)
        # print(l[0], l[1], l[2], l[3], l[4], l[5])  
        img = cv2.imread(image)  
        a = int(float(l[3]))  # xmin 
        b = int(float(l[5]))  # xmax
        c = int(float(l[2]))  # ymin 
        d = int(float(l[4]))  # ymax 
        if a<0:
            a=0
        if c<0:
            c=0            
        crop_image = img[a:b, c:d]  # 裁剪
        inf.save(crop_image,img, file_path + '/' + image_name, str(num), str(l[1]),str(a),str(b),str(c),str(d))  
        num=num+1

detection_results_path_word="../output_word/detection-results" + '/' + file_path
images_path_word="../output_word/images-optional" + '/' + file_path
detection_results = os.listdir(detection_results_path_word) 
for detection_result in detection_results: 
    # print(detection_result)
    image_name = detection_result.split('.')[0]
    image =  images_path_word+ '/' + image_name+'.png'
    # print(image)
    f = open(detection_results_path_word + '/' + detection_result, "r")
    lines = f.readlines()
    num=1
    for line in lines:
        l = line.split(' ')
        # print(l[0], l[1], l[2], l[3], l[4], l[5])  
        img = cv2.imread(image)  
        a = int(float(l[3]))  # xmin 
        b = int(float(l[5]))  # xmax
        c = int(float(l[2]))  # ymin 
        d = int(float(l[4]))  # ymax 
        if a<0:
            a=0
        if c<0:
            c=0  
        distance = sys.maxsize
        d_index = 0      
        for i in range(len(right_bottom)):
            c_dis = (d - int(right_bottom[i][0]))**2 + (b - int(right_bottom[i][1]))**2
            if c_dis < distance:
                distance = c_dis
                d_index = i
        crop_image = img[a:b, c:d]  # 裁剪
        roc_inf.save(crop_image,img, file_path + '/' + image_name, str(d_index+1), str(l[1]),str(a),str(b),str(c),str(d))  
        num=num+1

print(file_path + 'Cropping Completed!')



ocr_path = "../output_word/crop_results" + '/' + file_path
ocr_dirs = os.listdir(ocr_path)
ocr_dict = {}
for ocr_dir in ocr_dirs:
    ocr_pics = os.listdir("../output_word/crop_results" + '/' + file_path + '/' + ocr_dir)
    ocr_res = {}
    for ocr_pic in ocr_pics:
        ocr_pic_path = '/home/troykuo/ocr/py37_pytorch/output_word/crop_results' + '/' + file_path + '/' + ocr_dir + '/' + ocr_pic
        opt = {'Global.checkpoints': 'output/rec_CRNN/best_accuracy', 'Global.infer_img': ocr_pic_path}
        ocr_text = infer_rec.main(opt)
        ocr_res[ocr_text] = ocr_pic
    ocr_dict[ocr_dir] = ocr_res
print(ocr_dict)
# ocr_dict = {'Figure10-1': {'17': '2.png', '4': '22.png', '8': '21.png', '19': '1.png', '10': '7.png', '3': '12.png', '2': '9.png', '18': '14.png', '11': '15.png', '6': '4.png', '20': '3.png', '16': '11.png', '9': '23.png', '12': '20.png', '15': '19.png', '23': '8.png', '5': '16.png', '7': '6.png', '1': '13.png', '14': '10.png', '13': '18.png', '21': '5.png', '22': '17.png'}}

sentences_res = {}
for image_id in image_ids:
    text = info[image_id]
    sentences = spcv2.text_split_with_scispacy(text, nlp1)
    sentences = spcv2.text_split_check(sentences)
    sentences = spcv2.split_with_period(sentences)
    sentences = spcv2.text_split_with_semicolon(sentences)
    sentences = spcv2.complete(sentences)
    sentences_res[image_id] = sentences
    with open('../output/caption/' + file_path + '/' + image_id + '.txt', 'w', encoding='utf-8') as f:
        for sentence in sentences:
            f.write(sentence) 
            f.write('\n')
    f.close()

print("Caption Split Completed!")

for ocr_dir in ocr_dict.keys():
    subgraph_caption = {}
    subgraph_caption[0] = []
    # subgraph_caption.keys() = ocr_dict.keys()
    labels = []
    for key in ocr_dict[ocr_dir].keys():
        labels.append(key)
    print(labels)
    sorted_labels = spcv2.label_sort(labels)
    caption_res = spcv2.label_recognition(labels, sentences_res[ocr_dir])
    for key in caption_res.keys():
        for sub_label in caption_res[key]:
            if sub_label == 0:
                subgraph_caption[sub_label].append(sentences[key])
            else:
                pic = ocr_dict[ocr_dir][sub_label]
                if pic not in subgraph_caption.keys():
                    subgraph_caption[pic] = []
                subgraph_caption[pic].append(sentences[key])
    print(subgraph_caption)
    for key in subgraph_caption.keys():
        if not os.path.exists('../output/caption/' + file_path + '/' + ocr_dir + '/' + 'res'):
            os.mkdir("../output/caption/" + file_path + '/' + ocr_dir)
            os.mkdir('../output/caption/' + file_path + '/' + ocr_dir + '/' + 'res')
        with open("../output/caption/" + file_path + '/' + ocr_dir + '/' + 'res/' + str(key) + '.txt', 'w', encoding='utf-8') as f:
            for line in subgraph_caption[key]:
                f.write(line)
        f.close()
print("Complete!")
time_end = time.time()
print(time_end - time_start)









