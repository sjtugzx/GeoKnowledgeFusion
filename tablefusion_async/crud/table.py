import json
import logging
from typing import List, Dict, Union
from enum import Enum
from pydantic import BaseModel

from tablefusion_async import db

logger = logging.getLogger(__name__)


class TableDirection(str, Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


class TableOutline(BaseModel):
    table_id: int
    page: int
    x1: float
    y1: float
    x2: float
    y2: float
    direction: TableDirection
    confirmed: bool


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


# 获取表格内框线的一切标记，有一些标记自动设置到数据库 方便下一次快速获取
# 操作顺序不能乱，先判断旋转并旋转操作（改变了area），再判断ocr并ocr操作（改变了pdf路径和page_num），
# 生成xml，再以此判断 表格框线种类，阈值 等等
# async def get_and_set_table_meta(paper_id, table_id):
#     page, area = await crud.table.get_table_outline(paper_id, table_id)
#     table_id2info = await crud.table.get_table_info(paper_id, table_id)
#     table_type = table_id2info[table_id]["table_type"]
#     direction = table_id2info[table_id]["table_direction"]
#     ocr_flag = table_id2info[table_id]["ocr_flag"]
#     autothres = table_id2info[table_id]["auto_thres"]
#
#     content_id2pdf_bytes: Dict[int, bytes] = await crud.pdf.get_pdf_content(paper_id, models.PdfContentTypeEnum.PDF)
#     pdf_bytes = content_id2pdf_bytes[0]
#
#     # 获取pdf文件地址，是否需要旋转
#     if direction != "up":
#         area = get_area_direction(direction, area)
#         _, pdf_path = rotate_pdf(paper_id, pdf_bytes, page, direction)
#         page = 0
#     else:
#         pdf_path = await crud.pdf.make_pdf_to_static(paper_id)
#
#     xml_path = get_xml_path(pdf_path, page)
#
#     if ocr_flag == "unchecked" or ocr_flag == "":
#         ocr_flag = get_ocr_flag(xml_path)
#         if await crud.table.update_ocr_flag(paper_id, table_id, ocr_flag):
#             print("保存ocr状态错误 ！")
#
#     if ocr_flag == "notext":
#         page = 0
#         pdf_path = ocr_pdf(pdf_path, page, PDF_PROCESS_DIR)
#
#     if autothres == 0:
#         autothres = get_auto_thres(pdf_path, page, area, xml_path)
#         print(f"autothres状态变更为 {autothres}")
#         await crud.table.update_auto_thres(paper_id, table_id, autothres)
#
#     if table_type == "unchecked":
#         table_type = get_table_type(pdf_path, page, area)
#         print(f"表格 状态变更为 {table_type}")
#         if await crud.table.update_table_type(paper_id, table_id, table_type):
#             print("保存表格类型错误 ！")
#
#     return {
#         "ocr_flag": ocr_flag,
#         "area": area,
#         "direction": direction,
#         "table_type": table_type,
#         "autothres": autothres,
#         "pdfpath": pdf_path,
#         "xmlpath": xml_path,
#         "page": page,
#     }
