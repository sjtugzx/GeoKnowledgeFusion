import json
import base64
import logging

import requests
from billiard.exceptions import TimeLimitExceeded

from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure
from tablefusion_async import config, crud

from .utils import table_overlap, check_table_exists

logger = logging.getLogger(__name__)


@app.task(bind=True, base=BaseTask, time_limit=60 * 5)
def outline_detect(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None
    user_id = kwargs["user_id"] if kwargs and "user_id" in kwargs else None
    page2image = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE, DB=DB)
    if not page2image:
        raise TaskFailure(f'images of {paper_id} not found')

    table_outlines, have_table = crud.table.get_outline(paper_id, DB=DB)
    if have_table == 0:
        pdf_bytes = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF, DB=DB).get(0, b'')
        if not pdf_bytes:
            raise TaskFailure(f'pdf {paper_id} not found')

        try:
            have_table = 1 if check_table_exists(pdf_bytes) else 2
        except Exception as e:
            have_table = 1
            print(e)
        crud.table.save_have_table(paper_id, have_table, DB=DB)

    if have_table == 2:
        raise TaskFailure(f'{paper_id} not table')
    new_table_outlines = []

    if table_outlines:
        next_table_id = max(table_outlines, default=0, key=lambda x: x.table_id).table_id + 1
    else:
        next_table_id = 1

    host = config.SERVICE_BACKEND_INFO["table_outline"]["host"]
    port = config.SERVICE_BACKEND_INFO["table_outline"]["port"]
    for page, image in page2image.items():
        img_base64 = base64.b64encode(image).decode('ascii')
        datas = json.dumps({'base64': img_base64})

        tablecorlist_txt = requests.post(f'http://{host}:{port}/detect', data=datas)
        tablecorlist = json.loads(tablecorlist_txt.text)
        print("90 tablecorlist : ", tablecorlist)

        for tablecol in tablecorlist['tablecorlist']:
            table_oueline = crud.table.TableOutline(
                table_id=next_table_id,
                page=page,
                x1=tablecol[0],
                y1=tablecol[1],
                x2=tablecol[2],
                y2=tablecol[3],
                direction='up',
                confirmed=False,
            )
            if not any(table_overlap(existing_outline, table_oueline) for existing_outline in table_outlines):
                new_table_outlines.append(table_oueline)
                next_table_id += 1

    try:
        print("save_outline:")
        crud.table.save_outline(paper_id, new_table_outlines, DB=DB)
        crud.paper_list.update_paper_list_status(paper_id, "processed", _type="table_status")
    except Exception as e:
        logger.error(f"Could not write out result for table_outlines of paper {paper_id}", exc_info=e)
        raise TaskFailure(f"Could not write out result for table_outlines of paper {paper_id}")

    return f'table_outlines have been extracted and saved'


"""
要用到pdf文件，修改docker配置，添加挂载
inner_detect 获取表格内框线，表格内容文本
"""


@app.task(bind=True, base=BaseTask, time_limit=180)
def inner_detect(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None

    # 求外框线内的相对坐标a,b,c,d，在整个pdf中的相对位置，注意外框要加上旋转才是真正进行计算的pdf（生成了旋转的pdf）中外框的位置
    def get_trans_rec(x1, y1, x2, y2, outline):
        area = crud.table.get_area_direction(outline.direction.value, [outline.x1, outline.y1, outline.x2, outline.y2])
        width = area[2] - area[0]
        height = area[3] - area[1]
        return [area[0] + x1 * width, area[1] + y1 * height, area[0] + x2 * width, area[1] + y2 * height]

    table_ids = crud.table.get_inner(paper_id)
    for table_id in table_ids:
        meta = crud.table.get_and_set_table_meta(paper_id, table_id)
        page = meta["page"]
        pdfpath = meta["pdfpath"]
        xmlpath = meta["xmlpath"]
        structure = crud.table.detect_table_structure(paper_id, meta)
        if crud.table.save_table_structure(paper_id, table_id, structure, 0):
            raise TaskFailure(f"表格内结构保存错误 {paper_id}")
        print(f'table_inner have been extracted and saved')

        table = crud.table.get_table(paper_id, table_id)
        areas = []
        for row in structure.cells:
            for col in row:
                areas.append(
                    get_trans_rec(structure.columns[col.column_begin], structure.rows[col.row_begin],
                                  structure.columns[col.column_end], structure.rows[col.row_end], table.outline)
                )
        texts = crud.table.get_area_text(paper_id, pdfpath, page, xmlpath, areas)
        excel_path = crud.table.create_table_excel(paper_id, table_id, structure.cells, texts)

        table.content.excel_path = excel_path.replace("/tablefusoin-async/tablefusion_async", "/app/tablefusion")
        table.content.text = texts
        table.content.confirmed = False
        print("save_table_content:")
        if crud.table.save_table_content(paper_id, table_id, table.content, flag="new"):
            raise TaskFailure(f"表格内容保存错误 {paper_id}")
        print(f'table_content have been extracted and saved')

    return f'table_inner and table_content have been extracted and saved'


#############################################################################


@app.task(bind=True, base=BaseTask, time_limit=60 * 5, queue="table_fusion")
def outline_detect_1(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None
    user_id = kwargs["user_id"] if kwargs and "user_id" in kwargs else None
    page2image = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE, DB=DB)
    if not page2image:
        raise TaskFailure(f'images of {paper_id} not found')

    table_outlines, have_table = crud.table.get_outline(paper_id, DB=DB)
    if have_table == 0:
        pdf_bytes = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF, DB=DB).get(0, b'')
        if not pdf_bytes:
            raise TaskFailure(f'pdf {paper_id} not found')

        try:
            have_table = 1 if check_table_exists(pdf_bytes) else 2
        except Exception as e:
            have_table = 1
            print(e)
        crud.table.save_have_table(paper_id, have_table, DB=DB)

    if have_table == 2:
        raise TaskFailure(f'{paper_id} not table')
    new_table_outlines = []

    if table_outlines:
        next_table_id = max(table_outlines, default=0, key=lambda x: x.table_id).table_id + 1
    else:
        next_table_id = 1

    host = config.SERVICE_BACKEND_INFO["table_outline"]["host"]
    port = config.SERVICE_BACKEND_INFO["table_outline"]["port"]
    for page, image in page2image.items():
        img_base64 = base64.b64encode(image).decode('ascii')
        datas = json.dumps({'base64': img_base64})

        tablecorlist_txt = requests.post(f'http://{host}:{port}/detect', data=datas)
        tablecorlist = json.loads(tablecorlist_txt.text)
        print("90 tablecorlist : ", tablecorlist)

        for tablecol in tablecorlist['tablecorlist']:
            table_oueline = crud.table.TableOutline(
                table_id=next_table_id,
                page=page,
                x1=tablecol[0],
                y1=tablecol[1],
                x2=tablecol[2],
                y2=tablecol[3],
                direction='up',
                confirmed=False,
            )
            if not any(table_overlap(existing_outline, table_oueline) for existing_outline in table_outlines):
                new_table_outlines.append(table_oueline)
                next_table_id += 1

    try:
        print("save_outline:")
        crud.table.save_outline(paper_id, new_table_outlines, DB=DB)
        crud.paper_list.update_paper_list_status(paper_id, "processed", _type="table_status")
    except Exception as e:
        logger.error(f"Could not write out result for table_outlines of paper {paper_id}", exc_info=e)
        raise TaskFailure(f"Could not write out result for table_outlines of paper {paper_id}")

    return f'table_outlines have been extracted and saved'


@app.task(bind=True, base=BaseTask, time_limit=180, queue="table_fusion")
def inner_detect_1(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None

    # 求外框线内的相对坐标a,b,c,d，在整个pdf中的相对位置，注意外框要加上旋转才是真正进行计算的pdf（生成了旋转的pdf）中外框的位置
    def get_trans_rec(x1, y1, x2, y2, outline):
        area = crud.table.get_area_direction(outline.direction.value, [outline.x1, outline.y1, outline.x2, outline.y2])
        width = area[2] - area[0]
        height = area[3] - area[1]
        return [area[0] + x1 * width, area[1] + y1 * height, area[0] + x2 * width, area[1] + y2 * height]

    table_ids = crud.table.get_inner(paper_id)
    for table_id in table_ids:
        meta = crud.table.get_and_set_table_meta(paper_id, table_id)
        page = meta["page"]
        pdfpath = meta["pdfpath"]
        xmlpath = meta["xmlpath"]
        structure = crud.table.detect_table_structure(paper_id, meta)
        if crud.table.save_table_structure(paper_id, table_id, structure, 0):
            raise TaskFailure(f"表格内结构保存错误 {paper_id}")
        print(f'table_inner have been extracted and saved')

        table = crud.table.get_table(paper_id, table_id)
        areas = []
        for row in structure.cells:
            for col in row:
                areas.append(
                    get_trans_rec(structure.columns[col.column_begin], structure.rows[col.row_begin],
                                  structure.columns[col.column_end], structure.rows[col.row_end], table.outline)
                )
        texts = crud.table.get_area_text(paper_id, pdfpath, page, xmlpath, areas)
        excel_path = crud.table.create_table_excel(paper_id, table_id, structure.cells, texts)

        table.content.excel_path = excel_path.replace("/tablefusoin-async/tablefusion_async", "/app/tablefusion")
        table.content.text = texts
        table.content.confirmed = False
        print("save_table_content:")
        if crud.table.save_table_content(paper_id, table_id, table.content, flag="new"):
            raise TaskFailure(f"表格内容保存错误 {paper_id}")
        print(f'table_content have been extracted and saved')

    return f'table_inner and table_content have been extracted and saved'


#############################################################################

@app.task(bind=True, base=BaseTask, time_limit=60 * 5, queue="test2")
def outline_detect_2(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None
    user_id = kwargs["user_id"] if kwargs and "user_id" in kwargs else None
    page2image = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE, DB=DB)
    if not page2image:
        raise TaskFailure(f'images of {paper_id} not found')

    table_outlines, have_table = crud.table.get_outline(paper_id, DB=DB)
    if have_table == 0:
        pdf_bytes = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF, DB=DB).get(0, b'')
        if not pdf_bytes:
            raise TaskFailure(f'pdf {paper_id} not found')

        try:
            have_table = 1 if check_table_exists(pdf_bytes) else 2
        except Exception as e:
            have_table = 1
            print(e)
        crud.table.save_have_table(paper_id, have_table, DB=DB)

    if have_table == 2:
        raise TaskFailure(f'{paper_id} not table')
    new_table_outlines = []

    if table_outlines:
        next_table_id = max(table_outlines, default=0, key=lambda x: x.table_id).table_id + 1
    else:
        next_table_id = 1

    host = config.SERVICE_BACKEND_INFO["table_outline"]["host"]
    port = config.SERVICE_BACKEND_INFO["table_outline"]["port"]
    for page, image in page2image.items():
        img_base64 = base64.b64encode(image).decode('ascii')
        datas = json.dumps({'base64': img_base64})

        tablecorlist_txt = requests.post(f'http://{host}:{port}/detect', data=datas)
        tablecorlist = json.loads(tablecorlist_txt.text)
        print("90 tablecorlist : ", tablecorlist)

        for tablecol in tablecorlist['tablecorlist']:
            table_oueline = crud.table.TableOutline(
                table_id=next_table_id,
                page=page,
                x1=tablecol[0],
                y1=tablecol[1],
                x2=tablecol[2],
                y2=tablecol[3],
                direction='up',
                confirmed=False,
            )
            if not any(table_overlap(existing_outline, table_oueline) for existing_outline in table_outlines):
                new_table_outlines.append(table_oueline)
                next_table_id += 1

    try:
        print("save_outline:")
        crud.table.save_outline(paper_id, new_table_outlines, DB=DB)
        crud.paper_list.update_paper_list_status(paper_id, "processed", _type="table_status")
    except Exception as e:
        logger.error(f"Could not write out result for table_outlines of paper {paper_id}", exc_info=e)
        raise TaskFailure(f"Could not write out result for table_outlines of paper {paper_id}")

    return f'table_outlines have been extracted and saved'


@app.task(bind=True, base=BaseTask, time_limit=180, queue="test2")
def inner_detect_2(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None

    # 求外框线内的相对坐标a,b,c,d，在整个pdf中的相对位置，注意外框要加上旋转才是真正进行计算的pdf（生成了旋转的pdf）中外框的位置
    def get_trans_rec(x1, y1, x2, y2, outline):
        area = crud.table.get_area_direction(outline.direction.value, [outline.x1, outline.y1, outline.x2, outline.y2])
        width = area[2] - area[0]
        height = area[3] - area[1]
        return [area[0] + x1 * width, area[1] + y1 * height, area[0] + x2 * width, area[1] + y2 * height]

    table_ids = crud.table.get_inner(paper_id)
    for table_id in table_ids:
        meta = crud.table.get_and_set_table_meta(paper_id, table_id)
        page = meta["page"]
        pdfpath = meta["pdfpath"]
        xmlpath = meta["xmlpath"]
        structure = crud.table.detect_table_structure(paper_id, meta)
        if crud.table.save_table_structure(paper_id, table_id, structure, 0):
            raise TaskFailure(f"表格内结构保存错误 {paper_id}")
        print(f'table_inner have been extracted and saved')

        table = crud.table.get_table(paper_id, table_id)
        areas = []
        for row in structure.cells:
            for col in row:
                areas.append(
                    get_trans_rec(structure.columns[col.column_begin], structure.rows[col.row_begin],
                                  structure.columns[col.column_end], structure.rows[col.row_end], table.outline)
                )
        texts = crud.table.get_area_text(paper_id, pdfpath, page, xmlpath, areas)
        excel_path = crud.table.create_table_excel(paper_id, table_id, structure.cells, texts)

        table.content.excel_path = excel_path.replace("/tablefusoin-async/tablefusion_async", "/app/tablefusion")
        table.content.text = texts
        table.content.confirmed = False
        print("save_table_content:")
        if crud.table.save_table_content(paper_id, table_id, table.content, flag="new"):
            raise TaskFailure(f"表格内容保存错误 {paper_id}")
        print(f'table_content have been extracted and saved')

    return f'table_inner and table_content have been extracted and saved'

# @app.task(bind=True, base=BaseTask, queue="table_fusion")
# def test_1(self, *args):
#     print(f"1 : {args} {self.request.delivery_info['routing_key']}")
