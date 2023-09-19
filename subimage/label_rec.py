import sys
import io
import os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
import json
import string
import re

label_punc1 = '.,) '
label_punc2 = '-~\u2013\u00b1'
label_punc = label_punc1 + label_punc2
def label_recognition(labels, text):
    sen_class = {}
    for sens in text:
        index = text.index(sens)
        sen_class[index] = []
        tmp = sens
        if sens[0] == '(':
            tmp = sens[1:]
        flag = 1
        label_list = []
        while flag:
            label_index = 0            
            for label in labels:
                if label in label_list:
                    continue
                label_index = labels.index(label)
                label_len = len(label)
                if label_len > len(tmp) or tmp[0:0+label_len] != label:
                    continue
                else:
                    if tmp[label_len] not in label_punc:
                        label_list.append(label)
                        # flag = 0
                        break
                    else:
                        if tmp[label_len] in label_punc1 and tmp[label_len+1] == ' ':
                            sen_class[index].append(label)
                            tmp = tmp[label_len+2:]
                            # print (tmp)
                            break
                        elif tmp[label_len] in label_punc2:
                            label_index = labels.index(label)
                            fflag = 0
                            for l in labels[label_index+1:]:
                                llen = len(l)
                                if llen > len(tmp[label_len+1:]) or tmp[label_len+1:label_len+1+llen] != l:
                                    continue
                                else:
                                    l_index = labels.index(l)
                                    for lab in labels[label_index:l_index+1]:
                                        sen_class[index].append(lab)
                                    fflag = 1
                                    tmp = tmp[label_len+llen+3:]
                                    # print (tmp)
                                    break
                            if fflag == 0:
                                flag = 0
                                break
                            else:
                                break
                        else:
                            flag = 0
                            break
            if label_index == len(labels) - 1:
                if sen_class[index] == []:
                    sen_class[index].append(0)
                    flag = 0
                else:
                    flag = 0
            else:
                if sen_class[index] == []:
                    sen_class[index].append(0)
            for s in sen_class.keys():
                if 0 in sen_class[s] and len(sen_class[s]) > 1:
                    sen_class[s].pop(0)
    return sen_class

# with open('Figure10-1.txt', 'r', encoding='utf-8') as f:
#     text = f.readlines()
# labels = ['1', '2', '3']
# labels = ['A', 'A1', 'A2', 'A3', 'B', 'C', 'C1', 'C2']
# labels = ['A', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B', "B1", 'B2', 'B3', 'B4', 'B5', 'B6']
# labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
# labels= []
# for i in range(1, 24):
#     labels.append(str(i))
# # print(text)
# sen_class = label_recognition(labels, text)
# # print(text)
# print(sen_class)
# for sen in text:
#     print (str(sen_class[text.index(sen)]) + '\t' + sen)

def label_sort(labels):
    label_dict = {}
    for label in labels:
        l = len(label)
        if l not in label_dict.keys():
            label_dict[l] = []
        label_dict[l].append(label)
    res = []
    label_len = list(label_dict.keys())
    label_len.sort()
    for length in label_len:
        tmp_res = label_dict[length]
        tmp_res.sort()
        res.extend(tmp_res)
    return res

# import random
# labels= []
# for i in range(1, 24):
#     labels.append(str(i))
# random.shuffle(labels)
# print(labels)
# print(label_sort(labels))






