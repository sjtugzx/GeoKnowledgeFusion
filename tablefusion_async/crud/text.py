import json
import logging
from typing import List, Dict, Union
from enum import Enum

from tablefusion_async import db

logger = logging.getLogger(__name__)


def get_entity(
        project_id: int,
        paper_id: str,
) -> List[Dict]:
    sql = """
        SELECT entity FROM text_entity_v2 WHERE project_id = %s AND paper_id = %s
    """
    ret = db.mysql_select(sql, project_id, paper_id, cursor_type=db.Cursor)
    return json.loads(ret[0][0]) if ret else []


def save_entity(
        project_id: int,
        paper_id: str,
        entities: List[Dict],
) -> None:
    sql = """
        INSERT INTO text_entity_v2(project_id,paper_id,entity) VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE entity=VALUES(entity)
    """
    db.mysql_execute(sql, project_id, paper_id, json.dumps(entities))
