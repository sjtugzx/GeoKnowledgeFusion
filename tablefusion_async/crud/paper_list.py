import logging

from tablefusion_async import db

logger = logging.getLogger(__name__)


def update_paper_list_status(paper_id, user_id, status, _type):
    sql = f"UPDATE `paper_list` SET {_type} = %s WHERE pdf_md5 = %s AND import_user_id = %s;"
    db.mysql_execute(sql, status, paper_id, user_id)
