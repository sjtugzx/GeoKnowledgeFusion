from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import string
import re
import spacy
import scispacy
import spaCy as spcv2

app = FastAPI(
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    caption: str = None

class response_Item(BaseModel):
    caption_seg: List[str] = Field(...,example = ['a', 'b', 'c', 'd'])

@app.post('/cap_seg')
async def caption_segmentation(request_data: Item):
    caption = request_data.caption
    sentences = spcv2.text_split_with_scispacy(caption, nlp1)
    sentences = spcv2.text_split_check(sentences)
    sentences = spcv2.split_with_period(sentences)
    sentences = spcv2.text_split_with_semicolon(sentences)
    cap_seg_result = spcv2.complete(sentences)
    return cap_seg_result 


if __name__ == '__main__':
    spcv2.load_Abbreviations("Abbreviations.txt")
    nlp1 = spacy.load("en_core_sci_sm")
    print('SpaCy model loaded.')
    uvicorn.run(app=app, host="0.0.0.0", port=12346, workers=1)


