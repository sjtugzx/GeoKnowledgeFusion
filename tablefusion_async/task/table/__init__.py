import json
import base64
import logging

import requests

from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure
from tablefusion_async import config, crud

from .utils import table_overlap

logger = logging.getLogger(__name__)


@app.task(bind=True, base=BaseTask, time_limit=180)
def outline_detect(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None
    page2image = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE, DB=DB)
    if not page2image:
        raise TaskFailure(f'images of {paper_id} not found')

    table_outlines = crud.table.get_outline(paper_id, DB=DB)
    new_table_outlines = []
    next_table_id = max(table_outlines, default=0, key=lambda x: x['entity_id']) + 1

    host = config.SERVICE_BACKEND_INFO["table_outline"]["host"]
    port = config.SERVICE_BACKEND_INFO["table_outline"]["port"]
    for page, image in page2image.items():
        img_base64 = base64.b64encode(image).decode('ascii')
        datas = json.dumps({'base64': img_base64})

        tablecorlist_txt = requests.post(f'http://{host}:{port}/detect', data=datas)

        tablecorlist = json.loads(tablecorlist_txt.text)
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
        crud.table.save_outline(paper_id, new_table_outlines, DB=DB)
    except Exception as e:
        logger.error(f"Could not write out result for table_outlines of paper {paper_id}", exc_info=e)
        raise TaskFailure(f"Could not write out result for table_outlines of paper {paper_id}")

    return f'table_outlines have been extracted and saved'


"""
要用到pdf文件，修改docker配置，添加挂载
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
    table_ids = crud.table.get_inner(paper_id)
    for table_id in table_ids:
        meta = crud.table.get_and_set_table_meta(paper_id, table_id)

    return ""
