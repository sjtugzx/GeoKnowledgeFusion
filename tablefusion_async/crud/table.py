import io
import json
import logging
import os
import re
from datetime import datetime

import cv2
import PyPDF2
import ocrmypdf
import fitz
import numpy as np
import xlwt
from PIL import Image

from typing import List, Dict, Union, Any, Optional
from enum import Enum
from pydantic import BaseModel
from .model import *

from tablefusion_async import db, config

logger = logging.getLogger(__name__)


class TableDirection(str, Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


class TableOutline(BaseModel):
    table_id: int = 0
    page: int = 0  # 项目内部page从0开始计数
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    direction: TableDirection = "up"
    confirmed: bool = False


class TableStructure(BaseModel):
    area: List[float] = []
    rows: List[float] = []  # collums和rows是相对于area大框的相对位置
    columns: List[float] = []
    cells: List[List[TableCell]] = []
    confirmed: bool = False


class TableContent(BaseModel):
    excel_path: str = ''
    text: List[str] = []
    confirmed: bool = False


class Table(BaseModel):
    outline: TableOutline = TableOutline()
    structure: TableStructure = TableStructure()
    content: TableContent = TableContent()


def get_outline(
        paper_id: str,
        DB: str = None
) -> List[TableOutline]:
    if DB is None:
        DB = "dde_table_fusion"

    sql = '''
            SELECT table_id as table_id,pdf_page as page,raw_outer_line_x1 as raw_x1,raw_outer_line_y1 as raw_y1,
            raw_outer_line_x2 as raw_x2,raw_outer_line_y2 as raw_y2,final_outer_line_x1 as final_x1,
            final_outer_line_y1 as final_y1, final_outer_line_x2 as final_x2,final_outer_line_y2 as final_y2,
            table_direction as direction,confirmed
            FROM `table` WHERE pdf_md5 = %s AND is_deleted = '0'
        '''
    ret = db.mysql_select(sql, paper_id, cursor_type=db.DictCursor, db=DB)

    result = [
        TableOutline.parse_obj({
            'table_id': row['table_id'],
            'page': row['page'],
            'x1': row['final_x1'] if row['confirmed'] else row['raw_x1'],
            'y1': row['final_y1'] if row['confirmed'] else row['raw_y1'],
            'x2': row['final_x2'] if row['confirmed'] else row['raw_x2'],
            'y2': row['final_y2'] if row['confirmed'] else row['raw_y2'],
            'direction': row['direction'],
            'confirmed': row['confirmed'],
        }) for row in ret
    ]
    return result


def get_table(
        paper_id: str,
        table_id: int,
) -> Optional[Table]:
    table = Table()
    # table.enable_access()
    sql = '''
            SELECT table_id as table_id, pdf_page as pdf_page, raw_outer_line_x1 as raw_x1, raw_outer_line_y1 as raw_y1,
            raw_outer_line_x2 as raw_x2,raw_outer_line_y2 as raw_y2, final_outer_line_x1 as final_x1,
            final_outer_line_y1 as final_y1, table_direction as table_direction,
            final_outer_line_x2 as final_x2,final_outer_line_y2 as final_y2, confirmed,raw_inner_line as ri,
            final_inner_line as fi, raw_cell2content as rc, final_cell2content as fc
            FROM `table` WHERE pdf_md5 = %s  AND table_id =%s
        '''

    ret = db.mysql_select(sql, paper_id, table_id, cursor_type=db.DictCursor)
    # logger.info(ret)
    if len(ret) == 0:
        return None
    result = [
        {
            'id': row['table_id'],
            'page': row['pdf_page'],
            'x1': row['final_x1'] if row['confirmed'] else row['raw_x1'],
            'y1': row['final_y1'] if row['confirmed'] else row['raw_y1'],
            'x2': row['final_x2'] if row['confirmed'] else row['raw_x2'],
            'y2': row['final_y2'] if row['confirmed'] else row['raw_y2'],
            'direction': row["table_direction"],
            'confirmed': True,
        } for row in ret]

    table.outline = TableOutline.parse_obj(result[0])
    ret = ret[0]

    structurefi = TableStructure.parse_raw(ret["fi"]) if ret["fi"] is not None and len(
        ret["fi"]) != 0 else TableStructure()
    structureri = TableStructure.parse_raw(ret["ri"]) if ret["ri"] is not None and len(
        ret["ri"]) != 0 else TableStructure()

    # structureri.enable_access()
    # structurefi.enable_access()
    if structurefi != TableStructure() and structurefi != structureri:
        table.structure = structurefi
        # logger.info("建表过程:fin innerline:", structurefi)
    else:
        table.structure = structureri
        # logger.info("建表过程:raw innerline:", table.structure)

    if ret["rc"] is None or len(ret["rc"]) == 0:
        table.content = TableContent()
    else:
        if ret["fc"] is None or len(ret["fc"]) == 0:
            table.content = TableContent.parse_raw(ret["rc"])
        else:
            table.content = TableContent.parse_raw(ret["fc"])
    return table


def save_outline(
        paper_id: str,
        new_table_outlines: List[TableOutline],
        DB: str = None
) -> None:
    if DB is None:
        DB = "dde_table_fusion"
    sql = '''
            INSERT INTO `table` (pdf_md5,table_id,pdf_page,
            raw_outer_line_x1,raw_outer_line_y1,raw_outer_line_x2,raw_outer_line_y2,
            final_outer_line_x1,final_outer_line_y1,final_outer_line_x2,final_outer_line_y2,
            table_direction,confirmed,raw_inner_line,final_inner_line,auto_thres,inner_line_confirmed ,
            inner_line_change_flag,table_type,ocr_flag,raw_cell2content,
            final_cell2content,content_change_flag,cell_operation) VALUES 
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"","",0,0,"0","unchecked","unchecked","","","0","")
            ON DUPLICATE KEY UPDATE 
            final_outer_line_x1=VALUES(final_outer_line_x1),
            final_outer_line_y1=VALUES(final_outer_line_y1),
            final_outer_line_x2=VALUES(final_outer_line_x2),
            final_outer_line_y2=VALUES(final_outer_line_y2),
            confirmed=VALUES(confirmed),
            table_direction=VALUES(table_direction),
            raw_inner_line="",
            final_inner_line="",
            auto_thres=0,
            inner_line_confirmed=0,
            inner_line_change_flag='0',
            table_type='unchecked',
            ocr_flag='unchecked',
            raw_cell2content="",
            final_cell2content="",
            content_change_flag='0',
            cell_operation=""
        '''
    new_rows = [
        (paper_id, table.table_id, table.page - 1, table.x1, table.y1,
         table.x2, table.y2, table.x1, table.y1,
         table.x2, table.y2, table.direction.value, True)
        for table in new_table_outlines
    ]
    db.mysql_executemany(sql, new_rows, db=DB)


############################################################################################################

def get_inner(
        paper_id: str,
        DB: str = None
) -> List[int]:
    """检查pdf的表格的内框线是否已经构建，返回没有处理的表格id列表"""
    if DB is None:
        DB = "dde_table_fusion"

    sql = '''
             SELECT  table_id, raw_inner_line FROM `table` WHERE pdf_md5 = %s
        '''
    ret = db.mysql_select(sql, paper_id, cursor_type=db.DictCursor, db=DB)

    result = [row["table_id"] for row in ret if not row["raw_inner_line"]]
    return result


def get_table_outline(
        paper_id: str,
        table_id: int
):
    sql = '''
            SELECT pdf_page as page, raw_outer_line_x1 as raw_x1,raw_outer_line_y1 as raw_y1,
            raw_outer_line_x2 as raw_x2,raw_outer_line_y2 as raw_y2,final_outer_line_x1 as final_x1,
            final_outer_line_y1 as final_y1, final_outer_line_x2 as final_x2,final_outer_line_y2 as final_y2
            FROM `table` WHERE pdf_md5 = %s AND table_id= %s
        '''
    ret = db.mysql_select(sql, paper_id, table_id, cursor_type=db.DictCursor)
    if len(ret) == 0:
        return None
    logger.info("get_table_outline: ", ret[0])
    page = ret[0]["page"]
    rx1 = ret[0]["raw_x1"]
    rx2 = ret[0]["raw_x2"]
    ry1 = ret[0]["raw_y1"]
    ry2 = ret[0]["raw_y2"]
    fx1 = ret[0]["final_x1"]
    fx2 = ret[0]["final_x2"]
    fy1 = ret[0]["final_y1"]
    fy2 = ret[0]["final_y2"]
    if fx2 != 0 or fy2 != 0:
        return page, [fx1, fy1, fx2, fy2]
    else:
        return page, [rx1, ry1, rx2, ry2]


def get_table_info(
        paper_id: str,
        table_id: int,
) -> Union[Dict[Any, Any], int]:
    try:
        result = {}
        sql = "SELECT table_id, table_type, table_direction, ocr_flag, auto_thres " \
              "FROM `table` WHERE pdf_md5 = %s AND table_id =%s"
        ret = db.mysql_select(sql, paper_id, table_id, cursor_type=db.DictCursor)
        if ret and len(ret) != 0:
            for row in ret:
                result[row["table_id"]] = row
            return result
    except Exception as e:
        logger.exception(e)
        return 1


class PdfContentTypeEnum(str, Enum):
    PDF = 'pdf'
    GROBID_TEXT = 'grobid_text'  # Meta
    PDF2IMAGE_IMAGE = 'pdf2image_image'  # table


def get_pdf_content(
        pdf_md5: str,
        content_type: PdfContentTypeEnum,
        content_ids: Optional[List[int]] = None,
) -> Dict[int, bytes]:
    if content_ids:
        sql = '''
            SELECT content_id, content FROM pdf_content 
            WHERE pdf_md5=%s AND content_type=%s AND content_id in %s
        '''
        ret = db.mysql_select(sql, pdf_md5, content_type.value, content_ids)
    else:
        sql = '''
            SELECT content_id, content FROM pdf_content 
            WHERE pdf_md5=%s AND content_type=%s
        '''
        ret = db.mysql_select(sql, pdf_md5, content_type.value)
    id2content = {row[0]: row[1] for row in ret}

    return id2content


def get_area_direction(direction, area):
    x1 = area[0]
    y1 = area[1]
    x2 = area[2]
    y2 = area[3]
    if direction == "up":
        return area
    elif direction == "left":
        return [1 - y2, x1, 1 - y1, x2]
    elif direction == "down":
        return [1 - x2, 1 - y2, 1 - x1, 1 - y1]
    elif direction == "right":
        return [y1, 1 - x2, y2, 1 - x1]


def rotate_pdf(paper_id, pdf_bytes, table_id, page, rot="left"):
    """ 旋转pdf，返回旋转pdf的bytes；保存为pid_table_id_rot.pdf文件 PDF_PROCESS_DIR='static/processed/pdf' """
    pdf_reader = PyPDF2.PdfFileReader(pdf_bytes)
    pdf_writer = PyPDF2.PdfFileWriter()
    pagefile = pdf_reader.getPage(page)  # PDF 某页旋转
    if rot == "left":
        pagefile.rotateClockwise(90)
    elif rot == "down":
        pagefile.rotateClockwise(180)
    elif rot == "right":
        pagefile.rotateClockwise(270)
    pdf_writer.addPage(pagefile)
    pdf_bytes = io.BytesIO()
    pdf_writer.write(pdf_bytes)
    pdf_bytes.seek(0)
    pdf_bytes = pdf_bytes.getvalue()
    pdf_out = os.path.join(config.PDF_PROCESS_DIR, "{}_{}_rot.pdf".format(paper_id, table_id))
    with open(pdf_out, 'wb') as f:
        f.write(pdf_bytes)
    return pdf_bytes, pdf_out


def make_pdf_to_static(paper_id, pdf_bytes):
    """ paper 源文件 pdf PDF_DIR='static/upload/pdf' """
    pdf_out = os.path.join(config.PDF_DIR, "{}.pdf".format(paper_id))
    if not os.path.exists(pdf_out):
        with open(pdf_out, 'wb') as f:
            f.write(pdf_bytes)
    return pdf_out


# 生成xml文件，并返回地址
def get_xml_path(paper_id: str, pdf_path, page, force=False):
    xml_path = os.path.join(config.PDF_XML_DIR, paper_id + "_{}_pdfminer.xml".format(page))
    if os.path.exists(xml_path) and not force:
        return xml_path
    os.system("pdf2txt.py -o {} -p {} -t xml {}".format(xml_path, page + 1, pdf_path))
    return xml_path


def get_ocr_flag(xml_path):
    xml = open(xml_path, "r", encoding="utf-8").read()
    letter = re.findall("<text font=.*?bbox=\"(.*?)\".*?</text>", xml)
    if len(letter) == 0:
        return "notext"
    return "text"


def update_ocr_flag(
        paper_id: str,
        table_id: int,
        ocr_flag: str,
        # user_id: int,
) -> int:
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
            UPDATE `table` SET ocr_flag =%s, update_at =%s
            WHERE pdf_md5 = %s AND table_id = %s
        '''
    try:
        db.mysql_execute(sql, ocr_flag, dt, paper_id, table_id)
    except Exception as e:
        logger.info(f"ERROR! table.update_ocr_flag {e}")
        return 1
    return 0


# 生成有文字层的pdf
def ocr_pdf(paper_id: str, pdf_path, page):
    pdf_out = os.path.join(config.PDF_PROCESS_DIR, paper_id + "_{}_ocr.pdf".format(page))
    if os.path.exists(pdf_out):
        return pdf_out
    ocrmypdf.ocr(pdf_path, pdf_out, pages=str(page + 1), use_threads=False, language="eng+chi_sim",
                 pdfa_image_compression="lossless")
    return pdf_out


def get_table_prepocessed_img(pdf: Union[str, bytes], page: int, area: List[float], density=2000, propotion=-1.1):
    """获取表格预处理img"""
    if isinstance(pdf, bytes):
        doc = fitz.open('pdf', pdf)
    else:
        doc = fitz.open(pdf)
    page = doc[page]
    pix = page.get_pixmap()
    pdfheight = pix.height
    pdfwidth = pix.width
    clip = fitz.Rect([area[0] * pdfwidth, area[1] * pdfheight, area[2] * pdfwidth,
                      area[3] * pdfheight])
    if propotion < 0:
        pdfzoom = max(density / pdfheight, density / pdfwidth)
    else:
        pdfzoom = propotion
    mat = fitz.Matrix(pdfzoom, pdfzoom).prerotate(0)
    pix = page.get_pixmap(matrix=mat, alpha=False, clip=clip)
    pix = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    pix = np.array(pix)
    return pix[:, :, ::-1], pdfzoom


def get_auto_thres(pdf_path, page, area, xml_path):
    _, pdfzoom = get_table_prepocessed_img(pdf_path, page, area, propotion=3.5)
    xml = open(xml_path, "r", encoding="utf-8").read()
    letter = re.findall("<text font=.*?size=\"(.*?)\".*?</text>", xml)
    # 8.26 改变了阈值的判断方式
    if len(letter) == 0:
        # 没有文字层凭经验判断
        AUTOTHRES = 40
    else:
        n = 0
        sum = 0
        for box in letter:
            if float(box) == 0:
                continue
            sum += float(box)
            n += 1
        AUTOTHRES = int(sum / n * 0.55 * 1.2 * pdfzoom)
    print(f"自动阈值：{AUTOTHRES}")
    return AUTOTHRES


def get_table_type(pdf_path, page, area):
    table_img, _ = get_table_prepocessed_img(pdf_path, page, area, propotion=3.5)
    gray = cv2.cvtColor(table_img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, -5)
    # 识别竖线
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 60))
    eroded = cv2.erode(binary, kernel, iterations=1)
    dilatedrow = cv2.dilate(eroded, kernel, iterations=1)
    check = np.ones((dilatedrow.shape)) * 255
    check = dilatedrow == check
    thres = len(np.where(check == True)[0])
    print(f"线框检测:检测到线框像素: {thres}")
    if thres > 2000:
        print("线框检测:有线框表")
        return "framed"
    return "unframed"


def update_auto_thres(
        paper_id: str,
        table_id: int,
        autothres: int,
        # user_id: int,
) -> int:
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
            UPDATE `table` SET auto_thres =%s, update_at =%s
            WHERE  pdf_md5 = %s AND table_id = %s
        '''
    try:
        db.mysql_execute(sql, autothres, dt, paper_id, table_id)
    except Exception as e:
        logger.info(f"ERROR! CRUD语句错误，表格 间隔阈值 未更新！{e}")
        return 1
    return 0


def update_table_type(
        paper_id: str,
        table_id: int,
        table_type: str,
        # user_id: int,
) -> int:
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
            UPDATE `table` SET table_type =%s, update_at =%s
            WHERE pdf_md5 = %s AND table_id = %s
        '''
    try:
        db.mysql_execute(sql, table_type, dt, paper_id, table_id)
    except Exception as e:
        logger.info(f"ERROR! table.update_table_type {e}")
        return 1
    return 0


# 获取表格内框线的一切标记，有一些标记自动设置到数据库 方便下一次快速获取
# 操作顺序不能乱，先判断旋转并旋转操作（改变了area），再判断ocr并ocr操作（改变了pdf路径和page_num），
# 生成xml，再以此判断 表格框线种类，阈值 等等
def get_and_set_table_meta(paper_id, table_id):
    page, area = get_table_outline(paper_id, table_id)
    table_id2info = get_table_info(paper_id, table_id)
    table_type = table_id2info[table_id]["table_type"]
    direction = table_id2info[table_id]["table_direction"]
    ocr_flag = table_id2info[table_id]["ocr_flag"]
    autothres = table_id2info[table_id]["auto_thres"]

    content_id2pdf_bytes: Dict[int, bytes] = get_pdf_content(paper_id, PdfContentTypeEnum.PDF)
    pdf_bytes = content_id2pdf_bytes[0]

    # 获取pdf文件地址，是否需要旋转
    if direction != "up":
        area = get_area_direction(direction, area)
        _, pdf_path = rotate_pdf(paper_id, pdf_bytes, page, direction)
        page = 0
    else:
        pdf_path = make_pdf_to_static(paper_id, pdf_bytes)

    xml_path = get_xml_path(paper_id, pdf_path, page)

    if ocr_flag == "unchecked" or ocr_flag == "":
        ocr_flag = get_ocr_flag(xml_path)
        if update_ocr_flag(paper_id, table_id, ocr_flag):
            print("保存ocr状态错误 ！")

    if ocr_flag == "notext":
        page = 0
        pdf_path = ocr_pdf(paper_id, pdf_path, page)

    if autothres == 0:
        autothres = get_auto_thres(pdf_path, page, area, xml_path)
        print(f"autothres状态变更为 {autothres}")
        update_auto_thres(paper_id, table_id, autothres)

    if table_type == "unchecked":
        table_type = get_table_type(pdf_path, page, area)
        print(f"表格 状态变更为 {table_type}")
        if update_table_type(paper_id, table_id, table_type):
            print("保存表格类型错误 ！")

    return {
        "ocr_flag": ocr_flag,
        "area": area,
        "direction": direction,
        "table_type": table_type,
        "autothres": autothres,
        "pdfpath": pdf_path,
        "xmlpath": xml_path,
        "page": page,
    }


class _TableStructure(BaseModel):
    area: List[float] = []
    rows: List[float] = []  # collums和rows是相对于area大框的相对位置
    columns: List[float] = []
    cells: List[List[TableCell]] = []
    confirmed: bool = False


class TableCell(BaseModel):
    # begin代表表格单元格开始的行或列序号,end代表结束的行或序号
    column_begin: int = 0
    row_begin: int = 0
    column_end: int = 0
    row_end: int = 0


class TableStructure(BaseModel):
    area: List[float] = []
    rows: List[float] = []  # collums和rows是相对于area大框的相对位置
    columns: List[float] = []
    cells: List[List[TableCell]] = []
    confirmed: bool = False


def _detect_table_structure_frame(
        oripic: np.ndarray,
        area: List[float],
        AUTOTHRES: int
):
    """定义检测表结构框架"""
    opt_pic = oripic.copy()
    gray = cv2.cvtColor(opt_pic, cv2.COLOR_BGR2GRAY)
    # 二值化
    binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, -5)
    # 识别竖线
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    eroded = cv2.erode(binary, kernel, iterations=1)
    # cv2.imshow("Eroded Image",eroded)
    dilatedcol = cv2.dilate(eroded, kernel, iterations=1)
    # 识别横线
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    eroded = cv2.erode(binary, kernel, iterations=1)
    dilatedrow = cv2.dilate(eroded, kernel, iterations=1)
    # 标识表格
    merge = cv2.add(dilatedcol, dilatedrow)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # 进行腐蚀处理
    merge = cv2.dilate(merge, kernel, iterations=3)
    # 标识交点
    bitwiseAnd = cv2.bitwise_and(dilatedcol, dilatedrow)
    check = np.ones((bitwiseAnd.shape)) * 255
    pointset = np.where(bitwiseAnd == check)
    pointset = [np.array([pointset[0][i], pointset[1][i]]) for i in range(len(pointset[0]))]
    if len(pointset) == 0:
        return None
    keypoints = []
    thres = AUTOTHRES / 1.3

    def distance(a, b):
        return np.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]))

    # 删除交点集中的冗余点，使所有冗余点归于其中心
    # n^2复杂度 ， 这一步可以优化
    for pointid, point in enumerate(pointset):
        flag = 0
        for centid, (centor, num) in enumerate(keypoints):
            if distance(point, centor) < thres:
                keypoints[centid] = [(centor * num + point) / (num + 1), num + 1]
                flag = 1
        if flag == 0:
            keypoints.append([point, 1])
    ##2021.8.26 如果有框线识别错误就转到无框线识别
    if len(keypoints) == 0:
        return _detect_table_structure_noframe(oripic, AUTOTHRES, area)
    keypoints = [keypoints[i][0] for i in range(len(keypoints))]
    keypoints = np.array(keypoints, dtype=np.int)

    # 平行对齐
    last = keypoints[0][0]
    sum = last
    n = 1
    lastid = pointid = 0
    while pointid < len(keypoints):
        while pointid < len(keypoints) and keypoints[pointid][0] - last < 10:
            sum += keypoints[pointid][0]
            n += 1
            pointid += 1
        py = int(sum / n)
        for i in range(lastid, pointid):
            keypoints[i][0] = py
        if pointid >= len(keypoints):
            break
        lastid = pointid
        last = keypoints[pointid][0]
        sum = keypoints[pointid][0]
        n = 1
        pointid += 1
    keypoints = sorted(keypoints, key=lambda x: x[1])
    # print(f"按行排列: {keypoints}")
    last = keypoints[0][1]
    sum = last
    n = 1
    lastid = pointid = 0
    while pointid < len(keypoints):
        while pointid < len(keypoints) and keypoints[pointid][1] - last < 10:
            sum += keypoints[pointid][1]
            n += 1
            pointid += 1
        px = int(sum / n)
        for i in range(lastid, pointid):
            keypoints[i][1] = px
        if pointid >= len(keypoints):
            break
        lastid = pointid
        last = keypoints[pointid][1]
        sum = keypoints[pointid][1]
        n = 1
        pointid += 1
    keyx = {}
    keyy = {}
    for points in keypoints:
        if points[1] not in keyx.keys():
            keyx[points[1]] = 1
        else:
            keyx[points[1]] += 1
        if points[0] not in keyy.keys():
            keyy[points[0]] = 1
        else:
            keyy[points[0]] += 1
    delx = []
    dely = []
    for x in keyx:
        if keyx[x] == 1:
            delx.append(x)
    for y in keyy:
        if keyy[y] == 1:
            dely.append(y)
    keypoints = [point for point in keypoints if (point[0] not in dely) and (point[1] not in delx)]
    keypoints = np.array(keypoints)
    if len(keypoints) == 0:
        return None
    keypoints = keypoints[:, ::-1]
    keypoints = [(p[0], p[1]) for p in keypoints]
    # 从这里开始keypoint的点坐标为 横,纵
    # print(f"对齐、删除孤立点、按行排列后的点个数为: {len(keypoints)}")
    # print(f"顶点个数: {len(keypoints)}")
    Ys = set()
    Xes = set()
    for point in keypoints:
        Ys.add(point[1])
        Xes.add(point[0])
    Xes = list(Xes)
    Xes.sort()
    Ys = list(Ys)
    Ys.sort()
    if len(Ys) <= 2 or len(Xes) <= 2:
        return _detect_table_structure_noframe(oripic, AUTOTHRES, area)

    blocks = [[] for i in range(len(Ys) - 1)]

    # print(f"基本列数: {len(Xes) - 1}")
    # print("基本行数: {len(Ys) - 1}")

    def judgeLine(pa, pb, thres=10):
        if pa[0] == pb[0]:
            for i in range(-1 * int(thres / 2), 1 * int(thres / 2)):
                if pa[0] + i >= merge.shape[1] or pa[0] + i < 0:
                    continue
                if np.sum(merge[pa[1]:pb[1], pa[0] + i]) / (pb[1] - pa[1] + 1) > 200:
                    return True
        if pa[1] == pb[1]:
            for i in range(-1 * int(thres / 2), 1 * int(thres / 2)):
                if pa[1] + i >= merge.shape[0] or pa[1] + i < 0:
                    continue
                if np.sum(merge[pa[1] + i, pa[0]:pb[0]]) / (pb[0] - pa[0] + 1) > 140:
                    return True
        return False

    for yid, y in enumerate(Ys):
        for xid, x in enumerate(Xes):
            if (x, y) not in keypoints:
                continue
            if Xes.index(x) == len(Xes) - 1 or Ys.index(y) == len(Ys) - 1:
                continue
            flag = 0
            for txid in range(xid + 1, len(Xes)):
                if (Xes[txid], y) not in keypoints:
                    continue
                if not judgeLine((x, y), (Xes[txid], y)):
                    break
                for tyid in range(yid + 1, len(Ys)):
                    if (Xes[txid], Ys[tyid]) in keypoints:
                        if not judgeLine((Xes[txid], Ys[tyid - 1]), (Xes[txid], Ys[tyid])):
                            break
                        if not judgeLine((x, Ys[tyid - 1]), (x, Ys[tyid])):
                            break
                        if judgeLine((Xes[txid - 1], Ys[tyid]), (Xes[txid], Ys[tyid])):
                            blocks[yid].append([Xes[xid], Ys[yid], Xes[txid], Ys[tyid], txid - xid, tyid - yid, 1])
                            flag = 1
                            break
                if flag == 1:
                    break
    ret = TableStructure()
    ret.confirmed = False
    cellist = [[] for i in range(len(Ys) - 1)]
    for rowid, row in enumerate(blocks):
        for blockid, block in enumerate(row):
            cell = TableCell()
            cell.column_begin = Xes.index(block[0])
            cell.row_begin = Ys.index(block[1])
            cell.column_end = Xes.index(block[2])
            cell.row_end = Ys.index(block[3])
            cellist[rowid].append(cell)
    ret.cells = cellist
    ret.area = area
    ret.rows = [(i / opt_pic.shape[0]) for i in Ys]
    ret.columns = [(i / opt_pic.shape[1]) for i in Xes]
    return ret


def _detect_table_structure_noframe(
        oripic: np.ndarray,
        AUTOTHRES: int,
        area: List[float],
):
    # 根据thres确定的线宽,表格线删除需要 确定线宽,之后的划线也用到了线宽
    linewith = max(1, int(AUTOTHRES / 4))
    # print(f"自动线宽: {linewith}")
    # self.pic是原图,所有后续操作不对原图进行, 而是对副本opt_pic进行优化,pic_show是为了展示效果的副本
    opt_pic = oripic.copy()
    W = opt_pic.shape[1]
    H = opt_pic.shape[0]
    # 将图像转为灰度图,并提取边缘.
    opt_pic = cv2.cvtColor(opt_pic, cv2.COLOR_BGR2GRAY)
    # # 在图片最下面画一条横线，以防模型没有截好
    # cv2.line(opt_pic, (0, H - 1), (W - 1, H - 1), 0, max(1, linewith))
    # # 在图片最上面画一条横线，以防图片没有竖线
    # cv2.line(opt_pic, (0,0), (W - 1, 0), 0, max(1, linewith))
    #
    # edge = cv2.Canny(opt_pic, 20, 40, apertureSize=3)
    # # 通过边缘来确定表格中的直线以及端点
    # lines = cv2.HoughLinesP(edge, 1, np.pi / 180, threshold=220, minLineLength=300, maxLineGap=max(linewith, 3))
    # lines = [lines[i][0] for i in range(len(lines))]
    # # update 5.17 不用在此处去除线条
    # # 擦除表格中原有的划线.并确定表格位置, box中的元素依次是表格的 右左下上
    # box = [-99999, 99999, -99999, 99999]
    # for x1, y1, x2, y2 in lines:
    #     # 右x
    #     box[0] = max(x1, x2, box[0])
    #     # 左x
    #     box[1] = min(x1, x2, box[1])
    #     # 下y
    #     box[2] = max(y1, y2, box[2])
    #     # 上y
    #     box[3] = min(y1, y2, box[3])
    # XMIN = max(0, box[1])
    # XMAX = min(W - 1, box[0])
    # YMAX = min(H - 1, box[2])
    # YMIN = max(0, box[3])

    # update 21.11.17 表格区域就是用户框选的全部区域
    XMIN = 0
    XMAX = W - 1
    YMAX = H - 1
    YMIN = 0

    # update5.17
    # 完全去除线
    # 二值化
    mat, opt_pic = cv2.threshold(opt_pic, 200, 255, cv2.THRESH_BINARY)
    opt_pic = 255 - opt_pic
    # 识别横线
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (100, 1))
    eroded = cv2.erode(opt_pic, kernel, iterations=1)
    # cv2.imshow("Eroded Image",eroded)
    dilatedcol = cv2.dilate(eroded, kernel, iterations=1)
    # 识别竖线
    scale = 20
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 100))
    eroded = cv2.erode(opt_pic, kernel, iterations=1)
    dilatedrow = cv2.dilate(eroded, kernel, iterations=1)
    # 标识表格
    merge = cv2.add(dilatedcol, dilatedrow)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # 进行腐蚀处理
    merge = cv2.dilate(merge, kernel, iterations=3)
    # 两张图片进行减法运算，去掉表格框线
    merge2 = cv2.subtract(opt_pic, merge)
    opt_pic = 255 - merge2
    # 对优化图片进行腐蚀操作以及二值化以方便处理
    # ks是通过阈值算出来的核大小
    ks = max(2, int(AUTOTHRES / 4))
    print(f"自动腐蚀处理阈值: {ks}")
    kernel = np.ones((ks, ks), np.uint8)
    opt_pic = cv2.erode(opt_pic, kernel, iterations=1)
    mat, opt_pic = cv2.threshold(opt_pic, 200, 255, cv2.THRESH_BINARY)
    # 中值滤波,联结色块
    ks = int(ks / 2)
    ks = max(3, ks if ks % 2 == 1 else ks - 1)
    print(f"自动模糊处理阈值: {ks}")
    opt_pic = cv2.medianBlur(opt_pic, ks)
    # 取反色,这样所有空白区域的亮度值加起来是0
    opt_pic = 255 - opt_pic
    # 划横线, 先对表格纵向做一定的扩张,以确定更多的横线
    # xmin = box[1]
    # ymin = max(0, box[3] - 10)
    # xmax = min(box[0], W - 1)
    # ymax = min(H - 1, box[2] + 10)

    # 21.11.17 表格区域就是用户框选的区域
    xmin = XMIN
    ymin = YMIN
    xmax = XMAX
    ymax = YMAX
    # 记录下我们要划的线的两个端点
    linetodrawx = []
    # 我们接下来一行行扫描图像以确定划分表格的横线.
    # 若遇到某一行所有像素的亮度值之和为0,那么说明这一行没有元素,
    # 直到找到下一个像素值求和不为0的行,取这两行中间作为划分表格两行的分界线,
    # 并记录直线的两个端点(x1,y1,x2,y2)在linetodraw数组内
    Ys = []
    # aaa=100
    # for idp in range(ymin,  YMAX):
    #     tmp= sum(opt_pic[idp][xmin:xmax]) / (xmax - xmin)
    #     if tmp>0 and tmp<aaa:
    #         aaa=tmp
    #         print(aaa)

    while ymin <= ymax:
        if sum(opt_pic[ymin][xmin:xmax]) / (xmax - xmin) <= 3.5:
            liney = float(ymin)
            ymin += 1
            while ymin <= ymax and sum(opt_pic[ymin][xmin:xmax]) / (xmax - xmin) <= 3.5:
                ymin += 1
                liney += 0.5
            liney = int(liney + 0.5)
            Ys.append(liney)
            linetodrawx.append([XMIN, liney, XMAX, liney])
        ymin += 1

    ylines = [y1 for x1, y1, x2, y2 in linetodrawx]

    # print(f"自动分割阈值: {AUTOTHRES}")

    # 根据阈值来切割表格横行, boxes是所有空白框,boxes[row][id]=[左,上,右,下]
    boxes = [[] for i in range(0, len(ylines) - 1)]
    for id, Y in enumerate(ylines):
        if id + 1 == len(ylines):
            break
        xmin = XMIN
        xmax = XMAX
        while xmin <= xmax:
            while xmin <= xmax and sum(opt_pic[ylines[id]:ylines[id + 1] + 1, xmin]) > 0:
                xmin += 1
            if xmin <= xmax and sum(opt_pic[ylines[id]:ylines[id + 1], xmin]) == 0:
                left = int(xmin)
                xmin += 1
                THRES = AUTOTHRES
                while xmin <= xmax and sum(opt_pic[ylines[id]:ylines[id + 1] + 1, xmin]) == 0:
                    xmin += 1
                    THRES -= 1
                if THRES <= 0:
                    right = int(xmin - 1)
                    boxes[id].append([left, ylines[id], right, ylines[id + 1]])

    # 展示过程 opt_pic1描绘了所有盒子和横线
    opt_pic1 = opt_pic.copy()
    opt_pic1 = cv2.cvtColor(opt_pic1, cv2.COLOR_GRAY2BGR)
    for row in boxes:
        for x1, y1, x2, y2 in row:
            cv2.rectangle(opt_pic1, (x1, y1), (x2, y2), (255, 255, 255), max(1, int(linewith / 3)))
    for x1, y1, x2, y2 in linetodrawx:
        cv2.line(opt_pic1, (x1, y1), (x2, y2), (0, 255, 255), max(1, int(linewith / 3)))
    # self.imgSave(opt_pic1, "step_2")

    # 区分文字和空白区域块,空白区域 按行blocks[row][id]=[左,上,右,下,类型],type=0:blank ,1: content
    blocks = [[] for i in range(0, len(boxes))]
    # print(f"空白盒子: {boxes}")
    for rowid, row in enumerate(boxes):
        lastx = XMIN
        if len(row) == 0:
            continue
        if row[0][0] == XMIN:
            blocks[rowid].append([XMIN, boxes[rowid][0][1], row[0][2], boxes[rowid][0][3], 0])
            lastx = row[0][2]
            for x1, y1, x2, y2 in row[1:]:
                blocks[rowid].append([lastx, boxes[rowid][0][1], x1, boxes[rowid][0][3], 1])
                blocks[rowid].append([x1, boxes[rowid][0][1], x2, boxes[rowid][0][3], 0])
                lastx = x2
        else:
            lastx = XMIN
            for x1, y1, x2, y2 in row:
                blocks[rowid].append([lastx, boxes[rowid][0][1], x1, boxes[rowid][0][3], 1])
                blocks[rowid].append([x1, boxes[rowid][0][1], x2, boxes[rowid][0][3], 0])
                lastx = x2
        if lastx == XMAX:
            pass
        else:
            if blocks[rowid][-1][2] == 1:
                blocks[rowid].append([lastx, boxes[rowid][0][1], XMAX, boxes[rowid][0][3], 0])
            else:
                blocks[rowid].append([lastx, boxes[rowid][0][1], XMAX, boxes[rowid][0][3], 1])

    # 合并连通区域,
    # 先设定检查表,查看空白的存在情况
    # connects[row][id]=[rowbegin, rowend, xmin, xmax,rows ]
    connects = []
    check = [[] for i in range(0, len(boxes))]
    for rowid, row in enumerate(boxes):
        for box in row:
            check[rowid].append(1)
    for rowid, row in enumerate(boxes):
        for boxid, box in enumerate(row):
            if check[rowid][boxid] == 0:
                continue
            check[rowid][boxid] = 0
            rowbegin = rowid
            rowend = rowid + 1
            rowtmp = rowid + 1
            xmin, ymin, xmax, ymax = boxes[rowid][boxid]
            while rowtmp < len(boxes):
                flag = 0
                for tmpid, nextbox in enumerate(boxes[rowtmp]):
                    x1, y1, x2, y2 = nextbox
                    # if x1>=xmax or x2<=xmin or check[rowtmp][tmpid]==0:
                    if x1 >= xmax or x2 <= xmin or check[rowtmp][tmpid] == 0:
                        continue
                    if x1 >= xmin and x2 <= xmax:
                        xmin = x1
                        xmax = x2
                    elif x2 > xmax:
                        if x1 > xmin:
                            xmin = x1
                    elif x1 < xmin:
                        if x2 < xmax:
                            xmax = x2
                    rowend += 1
                    check[rowtmp][tmpid] = 0
                    flag = 1
                    break
                if rowend == len(boxes):
                    connects.append([rowbegin, rowend, xmin, xmax, rowend - rowbegin])
                    break
                elif flag == 1:
                    rowtmp += 1
                else:
                    connects.append([rowbegin, rowend, xmin, xmax, rowend - rowbegin])
                    break
    # print(f"联通个数: {len(connects)}")
    if len(connects) == 0:
        return None
        # raise ValueError("表格识别是错误的!")
    # 开始找通过最多连通分量的竖线横坐标
    linetodrawy = []
    # 判断某个联通区域是否还需要划分,1是需要,0是不需要
    check = [1 for thing in connects]
    # 只有一行的联通区域不需要划分了
    for id, thing in enumerate(connects):
        if thing[4] == 1:
            check[id] = 0

    def _getMaxPassInRegion(xmin, xmax, connects):
        maxpass = 0
        res = (xmin + xmax) / 2
        for x in range(xmin, xmax + 1):
            tmp = 0
            for con in connects:
                if x > con[2] and x < con[3]:
                    tmp += con[4]
            if tmp > maxpass:
                maxpass = tmp
                res = x
            if tmp == maxpass:
                res += 0.5
        return int(res), maxpass

    # 记录不必要查找的联通分量
    def _writeCheck(x, connects, check):
        for id, con in enumerate(connects):
            if con[2] <= x <= con[3]:
                check[id] = 0

    # Xes是划分的贯穿纵线的横坐标集合
    Xes = []
    for conid, con in enumerate(connects):
        if check[conid] == 0:
            continue
        check[conid] = 0
        xmin, xmax = [con[2], con[3]]
        x, maxpass = _getMaxPassInRegion(xmin, xmax, connects)
        # print("可连通{}行".format(maxpass))
        Xes.append(x)
        linetodrawy.append([x, YMIN, x, YMAX])
        _writeCheck(x, connects, check)

    Xes.sort()
    # 如果画的线通过文字区域这个线就要断开
    linetodrawY = []
    Xref = [[] for i in range(len(blocks))]
    for rowid, row in enumerate(blocks):
        for block in row:
            for x in Xes:
                if block[0] <= x <= block[2]:
                    if block[4] == 0:
                        linetodrawY.append([x, boxes[rowid][0][1], x, boxes[rowid][0][3]])
                        Xref[rowid].append(x)
    if Xes[0] > XMIN:
        Xes.insert(0, XMIN)
    if Xes[-1] < XMAX:
        Xes.insert(len(Xes), XMAX)

    # 通过行和x坐标 来获取单元格类型(是否有文字)
    def _getUnitType(rowid, X1, X2):
        for x1, y1, x2, y2, t in blocks[rowid]:
            if X1 <= x1 and X2 >= x2:
                return t
        return 0

    def _valToIndex(val, Li):
        id = 0
        for thing in Li:
            if val == thing:
                return id
            else:
                id += 1
        return 9999

    Units = [[] for id in range(len(Ys) - 1)]

    for rowid, row in enumerate(Xref):
        for id, X in enumerate(row):
            if id == 0:
                if X > XMIN:
                    t = _getUnitType(rowid, XMIN, X)
                    merge = _valToIndex(X, Xes)
                    unit = [XMIN, Ys[rowid], X, Ys[rowid + 1], merge, 1, t]
                    Units[rowid].append(unit)
            if id == len(row) - 1:
                t = _getUnitType(rowid, X, XMAX)
                merge = _valToIndex(XMAX, Xes) - _valToIndex(X, Xes)
                unit = [X, Ys[rowid], XMAX, Ys[rowid + 1], merge, 1, t]
                Units[rowid].append(unit)
                break
            Xb = row[id + 1]
            t = _getUnitType(rowid, X, Xb)
            merge = _valToIndex(Xb, Xes) - _valToIndex(X, Xes)
            unit = [X, Ys[rowid], Xb, Ys[rowid + 1], merge, 1, t]
            Units[rowid].append(unit)

    # 美化table,删除前排的空白框
    flag = 0
    for rowid in range(len(Units)):
        # if len(Units[rowid])<7:
        #     continue
        if Units[rowid][0][6] != 0:
            flag = 1
    if flag == 0:
        print("删除第一列空白列")
        for rowid in range(len(Units)):
            Units[rowid] = Units[rowid][1:]
        Xes = Xes[1:]

    flag = 0
    for rowid in range(len(Units)):
        # if len(Units[rowid])<7:
        #     continue
        if Units[rowid][-1][6] != 0:
            flag = 1
    if flag == 0:
        print("删除最后一列空白列")
        for rowid in range(len(Ys) - 1):
            Units[rowid] = Units[rowid][0:-1]
        Xes = Xes[:-1]
    # 删除多余末尾的空白
    flag = 0
    for rowid, row in enumerate(Units):
        # if len(Units[rowid])<7:
        #     continue
        if row[-1][4] == 1 and row[-1][6] != 0:
            flag = 1
    if flag == 0:
        print("检测到尾列有冗余列,自动调整")
        for rowid, row in enumerate(Units):
            # if len(Units[rowid]) < 7:
            #     continue
            if row[-1][4] > 1:
                row[-1][4] = 1
            elif row[-1][4] == 1:
                row[-2][4] = 1
                row[-2][2] = row[-1][2]
                Units[rowid] = row[:-1]
    # 删除多余首位的空白
    flag = 0
    for rowid, row in enumerate(Units):
        # if len(Units[rowid])<7:
        #     continue
        if row[0][4] == 1 and row[0][6] != 0:
            flag = 1
    if flag == 0:
        print("检测到首列有冗余列,自动调整")
        for rowid, row in enumerate(Units):
            # if len(Units[rowid]) < 7:
            #     continue
            if row[0][4] > 1:
                row[0][4] = 1
            elif row[0][4] == 1:
                row[1][4] = 1
                row[1][0] = row[0][0]
                Units[rowid] = row[1:]

    ret = TableStructure()
    ret.confirmed = False
    cellist = [[] for i in range(len(Ys) - 1)]
    for rowid, row in enumerate(Units):
        for unitid, unit in enumerate(row):
            cell = TableCell()
            cell.column_begin = Xes.index(unit[0])
            cell.row_begin = Ys.index(unit[1])
            cell.column_end = Xes.index(unit[2])
            cell.row_end = Ys.index(unit[3])
            cellist[rowid].append(cell)
    ret.cells = cellist
    ret.area = area
    oriheight = opt_pic.shape[0] / (area[3] - area[1])
    oriwidth = opt_pic.shape[1] / (area[2] - area[0])
    # ret.rows = [area[1] + i / oriheight for i in Ys]
    ret.rows = [i / opt_pic.shape[0] for i in Ys]
    # ret.columns = [area[0] + i / oriwidth for i in Xes]
    ret.columns = [i / opt_pic.shape[1] for i in Xes]
    return ret


def detect_table_structure(
        paper_id,
        meta
) -> _TableStructure:
    """检测表结构"""
    table_type = meta["table_type"]
    autothres = meta["autothres"]
    area = meta["area"]
    page = meta["page"]
    content_id2pdf_bytes: Dict[int, bytes] = get_pdf_content(paper_id, PdfContentTypeEnum.PDF)
    pdf_bytes = content_id2pdf_bytes[0]
    pix, _ = get_table_prepocessed_img(pdf_bytes, page, area, propotion=3.5)

    if table_type == "frame":
        # ret要么是None 要么是structure
        ret = _detect_table_structure_frame(pix, area, autothres)
        if ret:
            tablemerge = []
            rowid = 0
            colid = 0
            for row in ret.cells:
                for col in row:
                    if col.row_begin - col.row_end != 1 or col.column_begin - col.column_end != 1:
                        tablemerge.append({"row": rowid, "col": colid, "rowspan": col.row_begin - col.row_end,
                                           "colspan": col.column_begin - col.column_end})
                    rowid += col.row_begin - col.row_end
                    colid += col.column_begin - col.column_end
            return ret

    print("进行无框线表格处理")
    try:
        ret = _detect_table_structure_noframe(pix, autothres, area)
        return ret
    except Exception:
        raise RuntimeError("表格识别错误，请确实框选的是正确的表格！")


def save_table_structure(
        paper_id: str,
        table_id: int,
        table_structure: TableStructure,
        cleanflag=0,
) -> int:
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if cleanflag == 1:
        sql = '''
            UPDATE `table` SET final_inner_line= %s ,
            inner_line_change_flag='0',
            inner_line_confirmed=1,
            raw_cell2content = "",
            final_cell2content="",
            content_change_flag='0',
            cell_operation="",
            update_at =%s 
            WHERE  pdf_md5 = %s AND table_id = %s
        '''
    else:
        sql = '''
                    UPDATE `table` SET final_inner_line= %s  ,update_at =%s  
                    WHERE pdf_md5 = %s AND table_id = %s
                '''
    db.mysql_execute(sql, table_structure.json(), dt, paper_id, table_id)
    return 0


########################################################################################################################


def shrinkBboxes(para, bboxes):
    """# 原地缩小盒子,p从0-1 ,逐渐减小盒子到0"""

    def shrinkBbox(p, bbox):
        px = 1 / 2 * p * (bbox[2] - bbox[0])
        py = 1 / 2 * p * (bbox[3] - bbox[1])
        return [bbox[0] + px, bbox[1] + py, bbox[2] - px, bbox[3] - py, ]

    return [shrinkBbox(para, i) for i in bboxes]


def get_area_text(
        paper_id: str,
        pdf_path: str,
        page: int,
        xml_path: str,
        areas: List[List[float]]
) -> List[str]:
    xml = open(xml_path, "r", encoding="utf-8").read()
    # 得到fitz出来的pdf尺寸
    # 每段加一个空格,这样提取出来的东西是有空格的
    torep = re.findall("(<text font=.*?\">(.*)</text>\n<text> </text>)", xml)
    for thing in torep:
        str = thing[0].replace("\n<text> </text>", "")
        strnew = str + "\n" + str.replace(">{}<".format(thing[1]), "> <")
        xml = xml.replace(str, strnew)

    # 将字符串边界框变成float list
    def transbbox(box, height):
        tmp = [float(i) for i in box.split(",")]
        tmp1 = [tmp[0], height - tmp[3], tmp[2], height - tmp[1]]
        return tmp1

    def getpdfxmlshape(box):
        return [float(i) for i in box.split(",")]

    ori_size = getpdfxmlshape(re.findall("<page.*?bbox=\"(.*?)\".*?>", xml)[0])
    orishape = [ori_size[2], ori_size[3]]

    doc = fitz.open(pdf_path)
    pixo = doc[page].get_pixmap()
    h = pixo.height
    w = pixo.width

    for id in range(len(areas)):
        areas[id][0] = orishape[0] * areas[id][0]
        areas[id][1] = orishape[1] * areas[id][1]
        areas[id][2] = orishape[0] * areas[id][2]
        areas[id][3] = orishape[1] * areas[id][3]
    # print(areas)
    letter = re.findall("<text.*?bbox=\"(.*?)\".*?>(.*?)</text>", xml)
    # print(letter)
    bboxes = []
    letters = []
    for box in letter:
        tmp = transbbox(box[0], orishape[1])
        # update 21.11.17 fitz模块pdf页面转图片得到的尺寸和用pdfminer模块解析的xml中的页面尺寸可能不一，这里采用等比缩放
        tmp = [tmp[0] * w / orishape[0], tmp[1] * h / orishape[1], tmp[2] * w / orishape[0], tmp[3] * h / orishape[1]]
        bboxes.append(tmp)
        letters.append(box[1])

    bboxes = shrinkBboxes(0.5, bboxes)

    # doc = fitz.open(pdfpath)
    # page = doc[page]
    # pix = page.getPixmap()
    # pdfheight = pix.height
    # pdfwidth = pix.width
    # print(f"宽: {pdfwidth}")
    # print(f"高: {pdfheight}")
    # pix = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    # pix = np.array(pix)
    # pix = pix[:, :, ::-1].copy()
    # for id in range(len(areas)):
    #     area = np.array(areas[id], dtype=np.int64)
    #     cv2.rectangle(pix, (area[0], area[1]), (area[2], area[3]), (0, 0, 255), 1)
    # cv2.imshow("win",pix)
    # cv2.waitKey(0)

    # for area in bboxes:
    #     area = np.array(area, dtype=np.int64)
    #     cv2.rectangle(pix, (area[0], area[1]), (area[2], area[3]), (0, 255, 0), 1)
    # cv2.imshow("win",pix)
    # cv2.waitKey(0)
    # cv2.imwrite(os.path.join(IMG_DIR, hash_value + "_" + "{}".format(page) + "_ocred.jpg"), pix)
    # print("文字框:", bboxes)
    # print("要识别的框:", areas)
    texts = []
    for region in areas:
        x0, y0, x1, y1 = region
        size = len(bboxes)
        i = 0
        res = ""
        while i < size:
            bx0, by0, bx1, by1 = bboxes[i]
            if y0 > by1 or y1 < by0:
                i += 1
                continue
            elif y0 <= by0 and by1 <= y1:
                if x0 <= bx0 and x1 >= bx1:
                    res += letters[i]
                    i += 1
                    continue
            i += 1
        texts.append(res)
    return texts


def create_table_excel(
        paper_id: str,
        table_id: int,
        cells: List[List[TableCell]],
        texts: List[str],
        confirmed: bool = False,
        suffix: str = ""
) -> str:
    workbook = xlwt.Workbook(encoding="utf-8")
    worksheet = workbook.add_sheet("table")
    style = xlwt.XFStyle()
    align = xlwt.Alignment()
    align.horz = xlwt.Alignment.HORZ_CENTER
    align.vert = xlwt.Alignment.VERT_CENTER
    style.alignment = align
    index = 0
    cellsery = []
    for row in cells:
        for cell in row:
            cellsery.append(cell)
    for cell in cellsery:
        # print(cell)
        worksheet.write_merge(
            cell.row_begin, cell.row_end - 1, cell.column_begin, cell.column_end - 1, texts[index], style
        )
        index += 1

    nameseries = [paper_id, f"{table_id}"]
    if suffix != "":
        nameseries.append(suffix)
    if confirmed != False:
        nameseries.append("final.xls")
    else:
        nameseries.append("raw.xls")

    savepath = os.path.join(config.TABLE_CONTENT_FILE_DIR, "_".join(nameseries))
    workbook.save(savepath)
    return savepath


def save_table_content(
        paper_id: str,
        table_id: int,
        content: TableContent,
        flag="new"
) -> int:
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # logger.info(flag)
    sql = '''
                    UPDATE `table` SET final_cell2content =%s, content_change_flag = '1', update_at =%s
                    WHERE pdf_md5 = %s AND table_id = %s
                '''
    if flag == "new":
        sql = '''
                        UPDATE `table` SET raw_cell2content =%s, content_change_flag = '0', update_at =%s
                        WHERE pdf_md5 = %s AND table_id = %s
                    '''
    try:
        db.mysql_execute(sql, content.json(), dt, paper_id, table_id)
    except Exception as e:
        logger.exception(e)
        return 1
    return 0
