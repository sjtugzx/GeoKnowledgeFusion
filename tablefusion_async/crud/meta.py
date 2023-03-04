import logging
import re
from typing import List, Dict, Union
from enum import Enum

from lxml import etree

from tablefusion_async import db

logger = logging.getLogger(__name__)


# def get_paper_meta(
#         project_id: int,
#         paper_id: str,
# ) -> Dict:
#     sql = """
#         SELECT title, abstract, `year`, author FROM meta WHERE project_id = %s AND pdf_md5 = %s
#     """
#     ret = db.mysql_select(sql, project_id, paper_id, cursor_type=db.DictCursor)
#     if ret:
#         meta = ret[0]
#         meta['author'] = meta['author'].strip(';').split(';')
#         return meta
#     return {}


def _walk(node, text_list):
    tag = etree.QName(node).localname

    if node.text:
        if tag in ['head', 'p']:
            text_list.append(node.text)

    for child in node:
        _walk(child, text_list)


def _int_or_0(s: str):
    try:
        return int(s)
    except Exception:
        return 0


def _get_first(array: List):
    return array[0] if array else etree.Element('fake')


def save_paper_meta_to_mysql_from_grobid_text(grobid_content, paper_id, user_id):
    root = etree.XML(grobid_content)
    text_list = []
    _walk(root, text_list)

    ns = root.nsmap
    ns['ns'] = ns[None]
    ns.pop(None)

    title = ''.join(root.xpath('//ns:titleStmt/ns:title//text()', namespaces=ns))
    abstract = ''.join(root.xpath('//ns:abstract//text()', namespaces=ns)).strip()

    author_elements = root.xpath('//ns:teiHeader//ns:author/ns:persName', namespaces=ns)
    authors = []
    for author_element in author_elements:
        forename = ' '.join(author_element.xpath('.//ns:forename//text()', namespaces=ns)).strip()
        surname = ' '.join(author_element.xpath('.//ns:surname//text()', namespaces=ns)).strip()
        name = '%s %s' % (forename, surname)
        name = re.sub(r'\s+', ' ', name)
        authors.append(name)

    aff_elements = root.xpath('//ns:teiHeader//ns:author//ns:orgName[@type="institution"]', namespaces=ns)
    affiliations = []
    for aff_element in aff_elements:
        name = ' '.join(aff_element.xpath('.//text()')).strip()
        affiliations.append(name)

    journal = ''.join(
        root.xpath('//ns:teiHeader//ns:biblStruct//ns:monogr//ns:title[@type="main"]//text()', namespaces=ns)).strip()
    issn = ''.join(
        root.xpath('//ns:teiHeader//ns:biblStruct//ns:monogr//ns:idno[@type="ISSN"]//text()', namespaces=ns)).strip()
    publisher = ''.join(
        root.xpath('//ns:teiHeader//ns:biblStruct//ns:monogr//ns:publisher//text()', namespaces=ns)).strip()
    volume = _int_or_0(''.join(
        root.xpath('//ns:teiHeader//ns:biblStruct//ns:monogr//ns:biblScope[@unit="volume"]//text()',
                   namespaces=ns)).strip())
    issue = _int_or_0(''.join(
        root.xpath('//ns:teiHeader//ns:biblStruct//ns:monogr//ns:biblScope[@unit="issue"]//text()',
                   namespaces=ns)).strip())
    page_element = _get_first(
        root.xpath('//ns:teiHeader//ns:biblStruct//ns:monogr//ns:biblScope[@unit="page"]', namespaces=ns))
    if page_element.get('from'):
        first_page = _int_or_0(page_element.get('from', 0))
        last_page = _int_or_0(page_element.get('to', 0))
    else:
        first_page = last_page = _int_or_0(''.join(page_element.xpath('.//text()')).strip())
    date_element = _get_first(root.xpath('//ns:teiHeader//ns:biblStruct//ns:monogr//ns:date', namespaces=ns))
    year = _int_or_0(date_element.get('when', 0))
    doi = ''.join(root.xpath('//ns:teiHeader//ns:biblStruct//ns:idno[@type="DOI"]//text()', namespaces=ns)).strip()

    info = {
        'title': title,
        'abstract': abstract,
        'authors': ", ".join(authors),
        'affiliations': list(set(affiliations)),
        'journal': journal,
        'issn': issn,
        'publisher': publisher,
        'volume': volume,
        'issue': issue,
        'year': year,
        'first_page': first_page,
        'last_page': last_page,
        'doi': doi,
        'content': ' '.join(text_list),
        'link': '',
        'pdf_link': '',
        'language': 'english'
    }

    sql = """
         INSERT INTO meta (pdf_md5, title, abstract, `year`, author, journal, issn, volume, issue, first_page,
         last_page, doi, link, pdf_link, publisher, `language`, last_edit_user_id)
         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
         ON DUPLICATE KEY UPDATE title=VALUES(title), abstract=VALUES(abstract), `year`=VALUES(year), 
         author=VALUES(author), journal=VALUES(journal), issn=VALUES(issn), volume=VALUES(volume),
         issue=VALUES(issue), first_page=VALUES(first_page), last_page=VALUES(last_page), doi=VALUES(doi), 
         link=VALUES(link), pdf_link=VALUES(pdf_link), publisher=VALUES(publisher), `language`=VALUES(language)
     """
    db.mysql_execute(sql, paper_id, info["title"], info["abstract"],
                     info["year"], info["authors"], info["journal"], info["issn"],
                     info["volume"], info["issue"], info["first_page"], info["last_page"],
                     info["doi"], info["link"], info["pdf_link"], info["publisher"],
                     info["language"], user_id)

    sql2 = "UPDATE `paper_list` SET display_name = %s WHERE pdf_md5 = %s;"
    db.mysql_execute(sql2, info["title"], paper_id)

