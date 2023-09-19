import hashlib
import json
import pickle
import re
import os
import shutil
import sys
import traceback
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Union, Any
from tempfile import TemporaryDirectory, TemporaryFile
from zipfile import ZipFile
from pdf2image import convert_from_path
import numpy as np
from fastapi import HTTPException, status
from fastapi import UploadFile as _UploadFile
from lxml import etree
from pdf_parser import Parser

import common
import config
import models
import db
import fitz
from PIL import Image
import cv2



@app.post('/pdf')
def pdffigures2_parser(
        pdfpath: str
) -> Optional[Dict[int, Any]]:
    name=pdfpath.split('/')[-1].replace('pdf','pdffigures2.json')
    parser = Parser('pdffigures2')
    parser.parse('text', pdfpath, '/home/troykuo/tocr/py37_pytorch/fastapi_upload/pdfparse/', 50)

    json_path = '/home/troykuo/tocr/py37_pytorch/fastapi_upload/pdfparse/'+name
    return json_path