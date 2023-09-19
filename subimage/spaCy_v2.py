import sys
import io
import os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
import json
import string
import re
import spacy
import scispacy

num = '0123456789'
lower = 'qwertyuiopasdfghjklzxcvbnm'
upper = 'QWERTYUIOPASDFGHJKLZXCVBNM'
label_punc = '.,-~\u2013\u00b1)'
right_bracket_punc = ')]}'
left_bracket_punc = '([{'
Abbreviations = []

def load_Abbreviations(file_path):
    with open(file_path, encoding="utf-8") as fp:
        for line in fp.readlines():
            Abbreviations.append(line[:-1])
    fp.close()


def image_caption_extract(file_path):
    with open(file_path + '/figure-data.json', 'r', encoding='utf8') as fp:
        json_data = json.load(fp)
    res = []
    for i in json_data:
        if i['figType'] == 'Figure':
            tmp = {}
            tmp['caption'] = i['caption']
            tmp['name'] = i['name']
            tmp['renderURL'] = i['renderURL']
            res.append(tmp)
    with open(file_path + '/figure_captions.json', 'w', encoding='utf8') as f:
        json.dump(res, f)

def text_split_with_scispacy(text, nlp):
    doc = nlp(text)
    res = list(doc.sents)
    sentences = []
    for i in res:
        sentences.append(str(i))
    return sentences

def text_split_check(sentences):
    sens = []
    for index, sentence in enumerate(sentences):
        if index == 0:
            sens.append(sentence)
            continue
        elif index == len(sentences):
            break
        else:
            left_index = sens[-1].rfind('(')
            right_index = sens[-1].rfind(')')
            if left_index > right_index:
                sens[-1] += sentence
            else:
                sens.append(sentence)
    return sens 


def text_split_with_period(sentences):
    r = []
    for sentence in sentences:
        sens = re.split(r"[.] (?![^(]*\))", sentence) #用不在括号范围内的句号进行二次拆分，省去括号的判定。
        for c in sens:
            r.append(c)
    sens = r
    flag = 1
    while (flag):
        flag = 0
        res = []
        i = 0
        while (i < len(sens)):
            if i != 0 and len(sens[i]) < 6: # 分句过短进行合并
                if len(res[-1]) < 6 or i == len(sens) - 1:
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                elif ')' in sens[i] and '(' not in res[-1]:
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                elif sens[i] in Abbreviations or sens[i][:-1] in Abbreviations:
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                elif sens[i][0] not in upper and sens[i][0] not in lower and sens[i][0] not in num and sens[i][0] not in left_bracket_punc:
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                else:
                    if sens[i][-1] == '.':
                        res.append(sens[i] + ' ' + sens[i+1])
                    else:
                        res.append(sens[i] + '. ' + sens[i+1])
                    i += 2
                    flag = 1
            elif i != 0 and sens[i][0] not in upper and sens[i][0] not in lower and sens[i][0] not in num and sens[i][0] not in left_bracket_punc: # 以标点和特殊字符开头的子句合并
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
            elif sens[i][0] == '(': # 括号开头的分句合并的判断
                if i == 0:
                    res.append(sens[i])
                    i += 1
                else: 
                    l = 0
                    r = 0
                    for index in range(0, len(sens[i])):
                        if sens[i][index] == ')':
                            r = index
                            break
                    label_f = 0
                    for ele in sens[i][l:r]:
                        if ele in label_punc:
                            label_f += 1
                    if r - l > 6 and label_f < (r - l - 1) // 3:
                        if res[-1][-1] != '.':
                            res[-1] += '. ' + sens[i]
                        else:
                            res[-1] += ' ' + sens[i]
                        i += 1
                        flag = 1
                    elif r - l <= 6 and r - l > 3 and label_f == 0:
                        if res[-1][-1] != '.':
                            res[-1] += '. ' + sens[i]
                        else:
                            res[-1] += ' ' + sens[i]
                        i += 1
                        flag = 1
                    else:
                        res.append(sens[i])
                        i += 1
            elif i != 0 and sens[i][0] in lower and sens[i][1] not in label_punc and sens[i][2] not in label_punc: # 小写字母开头的单词为开头的分句合并的依据。
                l_n_flag = 0
                if sens[i][1] in num and sens[i][2] in num and sens[i][3] in label_punc:
                    res.append(sens[i])
                    i += 1
                    l_n_flag = 1
                if l_n_flag == 0:
                    if 'Abbreviations' not in res[-1]:
                        if res[-1][-1] != '.':
                            res[-1] += '. ' + sens[i]
                        else:
                            res[-1] += ' ' + sens[i]
                        i += 1
                        flag = 1
                    else:
                        res.append(sens[i])
                        i += 1
            elif i != 0 and sens[i][0] in upper and sens[i][1] not in label_punc and sens[i][1] not in label_punc: # 大写字母开头的单词为开头的分句与上一句合并。
                l_n_flag = 0
                if sens[i][1] in num and sens[i][2] in num and sens[i][3] in label_punc:
                    res.append(sens[i])
                    i += 1
                    l_n_flag = 1
                if l_n_flag == 0:
                    if len(res) > 1 and "Abbreviations" not in sens[i]:
                        if sens[i][0:3] != "Fig":
                            if res[-1][-1] != '.':
                                res[-1] += '. ' + sens[i]
                            else:
                                res[-1] += ' ' + sens[i]
                            i += 1
                            flag = 1
                        else:
                            res.append(sens[i])
                            i += 1
                    else:
                        res.append(sens[i])
                        i += 1
            elif i != 0 and sens[i][0] in num: # 非数字编号。
                num_f = ' '
                num_index = 0
                for ele in sens[i][1:4]:
                    if ele in label_punc:
                        num_f = ele
                        num_index = sens[i][1:4].index(ele) + 1
                        break
                if num_f == ' ':
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                elif num_f == '.' and res[-1][-3:] != "Fig" and res[-1][-3:] != "fig":
                    if sens[i][num_index-1] in num and sens[i][num_index+1] != ' ':
                        if res[-1][-1] != '.':
                            res[-1] += '. ' + sens[i]
                        else:
                            res[-1] += ' ' + sens[i]
                        i += 1
                        flag = 1
                    else:
                        res.append(sens[i])
                        i += 1
                else:
                    if res[-1][-3:] == "Fig" or res[-1][-3:] == "fig":
                        if res[-1][-1] != '.':
                            res[-1] += '. ' + sens[i]
                        else:
                            res[-1] += ' ' + sens[i]
                        i += 1
                        flag = 1
                    else:
                        res.append(sens[i])
                        i += 1
            elif i != 0 and (sens[i][1] in label_punc or sens[i][2] in label_punc):
                if sens[i][1] in label_punc and sens[i][1] not in "-~\u2013\u00b1" and sens[i][2] != ' ':
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                elif sens[i][2] in label_punc and sens[i][2] not in "-~\u2013\u00b1" and sens[i][3] != ' ':
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                elif sens[i][2] in label_punc and sens[i][2] not in "-~\u2013\u00b1" and sens[i][3] != ' ' and sens[i][1] not in num:
                    if res[-1][-1] != '.':
                        res[-1] += '. ' + sens[i]
                    else:
                        res[-1] += ' ' + sens[i]
                    i += 1
                    flag = 1
                else:
                    res.append(sens[i])
                    i += 1
            else:
                res.append(sens[i])
                i += 1
        sens = res
    return sens

def split_with_period(sentences):
    result = []
    result = text_split_with_period(sentences)
    name_detect = []
    name_detect.append(result[0])
    i = 1
    while i < len(result):
        if name_detect[-1][-1] in upper and name_detect[-1][-2] == ' ':
            if result[i][0] in upper and result[i][1:3] == '. ' and result[i][3] in upper:
                name_detect[-1] += '. ' + result[i]
                i += 1
            else:
                name_detect.append(result[i])
                i += 1
        else:
            name_detect.append(result[i])
            i += 1
    result = name_detect
    res = []
    res.append(result[0])
    for s in result[1:]:
        flag = 0
        for abb in Abbreviations:
            l = len(abb)
            if res[-1][-l:] == abb or res[-1][-l-1:-1] == abb:
                if s[0] != '(':
                    if res[-1][-1] == '.':
                        res[-1] += ' ' + s
                    else:
                        res[-1] += '. ' + s
                    flag = 1
                    break
        if flag == 0:
            res.append(s)
    return res

def text_split_with_semicolon(sentences):
    rres = []
    for sen in sentences:
        if "Abbreviations:" in sen or "Scale bars:" in sen or "Scale bar:" in sen or "abbreviations:" in sen:
            rres.append(sen)
            continue
        if ';' not in sen and ':' not in sen:
            rres.append(sen)
        else:
            clause = re.split("[:;] ", sen)
            tmp = []
            for i in range(0, len(clause)):
                if i != 0 and len(clause[i]) < 4:
                    if tmp[-1] + ';' in sen:
                        tmp[-1] += '; ' + clause[i]
                    else:
                        tmp[-1] += ': ' + clause[i]
                elif i != 0 and clause[i].count(')') >= clause[i].count('(') and tmp[-1].count('(') > tmp[-1].count(')'):
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                elif i != 0 and clause[i][0] in lower and clause[i][1] not in label_punc and clause[i][2] not in label_punc:
                    l_n_flag = 0
                    if clause[i][1] in num and clause[i][2] in num and clause[i][3] in label_punc:
                        tmp.append(clause[i])
                        l_n_flag = 1
                    if l_n_flag == 0:
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                elif i != 0 and clause[i][0] in upper and clause[i][1] not in label_punc and clause[i][2] not in label_punc:
                    l_n_flag = 0
                    if clause[i][1] in num and clause[i][2] in num and clause[i][3] in label_punc:
                        tmp.append(clause[i])
                        l_n_flag = 1
                    if l_n_flag == 0:
                        if clause[i][0:3] != "Fig":
                            if tmp[-1] + ';' in sen:
                                tmp[-1] += '; ' + clause[i]
                            else:
                                tmp[-1] += ': ' + clause[i]
                        else:
                            tmp.append(clause[i])
                elif i != 0 and clause[i][0] not in lower and clause[i][0] not in upper and clause[i][0] not in num and clause[i][0] != '(' and clause[i][0] not in label_punc:
                    if clause[i][1] not in label_punc and clause[i][2] not in label_punc:
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                    else:
                        tmp.append(clause[i])
                elif i != 0 and clause[i][0] in num:
                    punc = 0
                    for letter in clause[i][1:]:
                        if letter not in num:
                            punc = clause[i].find(letter)
                            break
                    if clause[i][punc:punc+2] == '. ':
                        tmp.append(clause[i])
                    elif clause[i][punc] != '.' and clause[i][punc] in label_punc:
                        tmp.append(clause[i])
                    else:
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                elif i != 0 and clause[i][0] == '(':
                    # if clause[i][-1] == ')' and clause[i].count('(') == 1:
                    #     if tmp[-1] + ';' in sen:
                    #         tmp[-1] += '; ' + clause[i]
                    #     else:
                    #         tmp[-1] += ': ' + clause[i]
                    # else:
                    #     l = clause[i].find(')')
                    #     if l < 0 or l > 7:
                    #         if tmp[-1] + ';' in sen:
                    #             tmp[-1] += '; ' + clause[i]
                    #         else:
                    #             tmp[-1] += ': ' + clause[i]
                    #     elif l > 0 and l < 5:
                    #         tmp.append(clause[i])
                    #     else:
                    #         flag1 = 0
                    #         for letter in clause[i][0:l]:
                    #             if letter in label_punc:
                    #                 tmp.append(clause[i])
                    #                 flag1 = 1
                    #                 break
                    #         if flag1 == 0:
                    #             if tmp[-1] + ';' in sen:
                    #                 tmp[-1] += '; ' + clause[i]
                    #             else:
                    #                 tmp[-1] += ': ' + clause[i]
                    if clause[i][-1] == ')' and clause[i].count('(') == 1:
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                    else:
                        l = 0
                        r = 0
                        for index in range(0, len(clause[i])):
                            if clause[i][index] == ')':
                                r = index
                                break
                        label_f = 0
                        for ele in clause[i][l:r]:
                            if ele in label_punc:
                                label_f += 1
                        if r - l > 6 and label_f < (r - l - 1) // 3:
                            if tmp[-1] + ';' in sen:
                                tmp[-1] += '; ' + clause[i]
                            else:
                                tmp[-1] += ': ' + clause[i]
                        elif r - l <= 6 and r - l > 3 and label_f == 0:
                            if tmp[-1] + ';' in sen:
                                tmp[-1] += '; ' + clause[i]
                            else:
                                tmp[-1] += ': ' + clause[i]
                        else:
                            tmp.append(clause[i])
                elif i != 0 and (clause[i][1] in label_punc or clause[i][2] in label_punc):
                    if clause[i][1] in label_punc and clause[i][1] not in "-~\u2013\u00b1" and clause[i][2] != ' ':
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                    elif clause[i][2] in label_punc and clause[i][2] not in "-~\u2013\u00b1" and clause[i][3] != ' ':
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                    elif clause[i][2] in label_punc and clause[i][2] not in "-~\u2013\u00b1" and clause[i][3] == ' ' and clause[i][1] not in num:
                        if tmp[-1] + ';' in sen:
                            tmp[-1] += '; ' + clause[i]
                        else:
                            tmp[-1] += ': ' + clause[i]
                    else:
                        tmp.append(clause[i])          
                else:
                    tmp.append(clause[i])
            for s in tmp:
                if tmp.index(s) != len(tmp) - 1:
                    if s + ';' in sen:
                        rres.append(s + ';')
                    else:
                        rres.append(s + ':')
                else:
                    rres.append(s)
    return rres

def complete(sentences):
    tmp = []
    for sentence in sentences:
        if sentence[-1] not in string.punctuation:
            tmp.append(sentence + '.')
        else:
            tmp.append(sentence)
    return tmp



def split(file_path, nlp):
    load_Abbreviations("Abbreviations.txt")
    with open(file_path + '/figure_captions.json', 'r', encoding='utf8') as fp:
        json_data = json.load(fp)
    for i in json_data:
        text = i['caption']
        file_name = i['renderURL'][:-4]
        sentences = text_split_with_scispacy(text, nlp)
        sentences = text_split_check(sentences)
        sentences = split_with_period(sentences)
        sentences = text_split_with_semicolon(sentences)
        sentences = complete(sentences)
        # with open(file_path + '/spaCysm/' + file_name + '.txt', 'w', encoding='utf8') as f:
        with open(file_path + '/spaCylg/' + file_name + '.txt', 'w', encoding='utf8') as f:
            for sentence in sentences:
                f.write(sentence) 
                f.write('\n')
        f.close()
        # print(file_path + '/spaCysm/' + file_name)
        # print(file_path + '/spaCylg/' + file_name)
        
    

# path = "compare2/output"
# dirs = os.listdir(path)

# nlp = spacy.load("en_core_sci_sm")
# nlp1 = spacy.load("en_core_sci_lg")
# for dir in dirs:
#     if not os.path.exists(path + '/' + dir + '/spaCysm'):
#         os.mkdir(path + '/' + dir + '/spaCysm')
#     image_caption_extract(path + '/' + dir)
#     text_split(path + '/' + dir, nlp)
#for dir in dirs:
#    if not os.path.exists(path + '/' + dir + '/spaCylg'):
#        os.mkdir(path + '/' + dir + '/spaCylg')
#    image_caption_extract(path + '/' + dir)
#    split(path + '/' + dir, nlp1)
#print("complete.")

