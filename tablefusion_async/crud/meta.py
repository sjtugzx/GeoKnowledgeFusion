import logging
from typing import List, Dict, Union
from enum import Enum

from tablefusion_async import db

logger = logging.getLogger(__name__)


def get_paper_meta(
        project_id: int,
        paper_id: str,
) -> Dict:
    sql = """
        SELECT title, abstract, `year`, author FROM meta WHERE project_id = %s AND pdf_md5 = %s
    """
    ret = db.mysql_select(sql, project_id, paper_id, cursor_type=db.DictCursor)
    if ret:
        meta = ret[0]
        meta['author'] = meta['author'].strip(';').split(';')
        return meta
    return {}
