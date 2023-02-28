import io
import os
import time
# import json
# import base64
import logging
# from tempfile import TemporaryDirectory, TemporaryFile
# from pathlib import Path

import fitz
from PIL import Image
import requests
# from science_parse_api.api import parse_pdf
# from pdfminer.converter import PDFPageAggregator
# from pdfminer.layout import LAParams, LTTextBox, LTTextLine
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdfinterp import PDFPageInterpreter
# from pdfminer.pdfinterp import PDFResourceManager
# from pdfminer.pdfpage import PDFPage
# from pdfminer.pdfparser import PDFParser

from tablefusion_async.main import app
from tablefusion_async.common import BaseTask, TaskFailure
from tablefusion_async import config, crud

logger = logging.getLogger(__name__)


@app.task(bind=True, base=BaseTask)
def grobid_text(
        self,
        paper_id: str,
        content_id: int = 0,
        *args,
        reset: bool = False,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None
    user_id = kwargs["user_id"] if kwargs and "user_id" in kwargs else None
    existing_content = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.GROBID_TEXT, DB=DB).get(0, b'')
    if not reset and len(existing_content) >= 300:  # 确定已有结果且不是之前写入的empty result
        return 'Result exists. Task skip'

    pdf_bytes = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF, DB=DB).get(0, b'')
    if not pdf_bytes:
        raise TaskFailure(f'pdf {paper_id} not found')

    files = {
        'input': (
            f'{paper_id}.pdf',
            pdf_bytes,
            'application/pdf',
            {'Expires': '0'}
        )
    }

    host = config.SERVICE_BACKEND_INFO["grobid"]["host"]
    port = config.SERVICE_BACKEND_INFO["grobid"]["port"]
    url = f'http://{host}:{port}/api/processFulltextDocument'
    data = {}
    if kwargs.get('generateIDs', False):
        data['generateIDs'] = '1'
    if kwargs.get('consolidate_header', False):
        data['consolidateHeader'] = '1'
    if kwargs.get('consolidate_citations', False):
        data['consolidateCitations'] = '1'
    if kwargs.get('teiCoordinates', False):
        data['teiCoordinates'] = ["persName", "figure", "ref", "biblStruct", "formula"]

    while True:
        r = requests.post(url=url, data=data, files=files, headers={'Accept': 'application/xml'})
        if r.status_code == 200:  # success
            content = r.content
            result = 'grobid parse success'
            break
        elif r.status_code != 503:  # not 503 means fatal error, do not re-try, return directly
            content = (b'<?xml version="1.0" encoding="UTF-8"?>\n'
                       b'<TEI xml:space="preserve" xmlns="http://www.tei-c.org/ns/1.0" \n'
                       b'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                       b'xsi:schemaLocation="http://www.tei-c.org/ns/1.0 /opt/grobid/grobid-home/schemas/xsd/Grobid.xsd"\n'
                       b'xmlns:xlink="http://www.w3.org/1999/xlink"/>')
            result = 'grobid parse failed, write empty xml file'
            logger.error(f"PDF Grobid parse failed: {paper_id} with http code {r.status_code}")
            break
        time.sleep(3)

    try:
        print("save_pdf_content:")
        crud.pdf.save_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.GROBID_TEXT, {0: content}, DB=DB)
        print("save_paper_meta_to_mysql_from_grobid_text:")
        crud.meta.save_paper_meta_to_mysql_from_grobid_text(content, paper_id, user_id)
    except Exception:
        raise TaskFailure(
            f"Could not write out result for {crud.pdf.PdfContentTypeEnum.GROBID_TEXT.value} paper {paper_id}")

    return result


@app.task(bind=True, base=BaseTask)
def fitz_image(
        self,
        paper_id: str,
        project_id: int = 0,
        content_id: int = 0,
        *args,
        reset: bool = False,
        density: int = 2300,
        **kwargs,
) -> str:
    DB = kwargs["DB"] if kwargs and "DB" in kwargs else None
    existing_content = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE, DB=DB)
    if not reset and len(existing_content) > 0:
        return 'Result exists. Task skip'

    pdf_bytes = crud.pdf.get_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF, DB=DB).get(0, b'')
    if not pdf_bytes:
        raise TaskFailure(f'pdf {paper_id} not found')

    try:
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        pagenumber = len(doc)
        imgs = []
        for i in range(pagenumber):
            page = doc[i]
            pix = page.get_pixmap()
            pdfheight = pix.height
            pdfwidth = pix.width
            pdfzoom = min(density / pdfheight, density / pdfwidth)
            mat = fitz.Matrix(pdfzoom, pdfzoom).prerotate(0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            imgs.append(pix)
    except Exception as e:
        logger.error(f"extract image failed for paper {paper_id}", exc_info=e)
        # raise TaskFailure(f"extract image failed for paper {paper_id}")
        imgs = []

    try:
        id2content = {}
        for page, img in enumerate(imgs):
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            id2content[page] = img_byte_arr.getvalue()
        crud.pdf.save_pdf_content(paper_id, crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE, id2content, DB=DB)
    except Exception as e:
        logger.error(
            f"Could not write out result for {crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE.value} paper {paper_id}",
            exc_info=e)
        raise TaskFailure(
            f"Could not write out result for {crud.pdf.PdfContentTypeEnum.PDF2IMAGE_IMAGE.value} paper {paper_id}")

    return f'{len(imgs)} images have been extracted and saved'
