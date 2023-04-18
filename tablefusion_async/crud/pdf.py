import logging
from typing import List, Dict, Union, Optional
from enum import Enum

from tablefusion_async import db

logger = logging.getLogger(__name__)


class PdfContentTypeEnum(str, Enum):
    PDF = 'pdf'
    GROBID_TEXT = 'grobid_text'
    # SCIENCEPARSE_TEXT = 'scienceparse_text'
    PDF2IMAGE_IMAGE = 'pdf2image_image'
    PDFFIGURES2_IMAGE = 'pdffigures2_image'
    PDFFIGURES2_IMAGE_META = 'pdffigures2_image_meta'
    # PDFFIGURES2_TEXT = 'pdffigures2_text'
    # PDFMINER_TEXT = 'pdfminer_text'
    # TEXT = 'text'


def save_pdf_content(
        pdf_md5: str,
        content_type: PdfContentTypeEnum,
        id2content: Dict[int, Union[bytes, str]],
        DB: str = None
) -> None:
    if DB is None:
        DB = "dde_table_fusion"

    sql = '''
        INSERT INTO pdf_content(pdf_md5,content_type,content_id,content) VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE content=VALUES(content)
    '''
    id_content = [
        (pdf_md5, content_type.value, content_id, content if isinstance(content, bytes) else content.encode('utf-8'))
        for content_id, content in id2content.items()
    ]
    db.mysql_executemany(sql, id_content, db=DB)


def get_pdf_content(
        pdf_md5: str,
        content_type: PdfContentTypeEnum,
        content_ids: Optional[List[int]] = None,
        DB: str = None
) -> Dict[int, bytes]:
    if DB is None:
        DB = "dde_table_fusion"

    if content_ids:
        sql = '''
            SELECT content_id, content FROM pdf_content 
            WHERE pdf_md5=%s AND content_type=%s AND content_id in %s
        '''
        ret = db.mysql_select(sql, pdf_md5, content_type.value, content_ids, db=DB)
    else:
        sql = '''
            SELECT content_id, content FROM pdf_content 
            WHERE pdf_md5=%s AND content_type=%s
        '''
        ret = db.mysql_select(sql, pdf_md5, content_type.value, db=DB)
    id2content = {row[0]: row[1] for row in ret}

    return id2content
