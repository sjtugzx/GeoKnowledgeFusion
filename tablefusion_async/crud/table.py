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
