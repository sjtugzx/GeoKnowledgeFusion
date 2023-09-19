# Components of GeoKnowledgeFusion

Code for the Paper "GeoKnowledgeFusion: A Platform for Multimodal Data Compilation from Geoscience Literature".

## Environment
* Operating System: Linux System
* Languages & Libraries:
* python==3.9
* pytorch==1.10.1
* torchvision==0.11.2
* torchaudio==0.10.1
* Tools & Utilities:
* cudatoolkit=11.3
* Cuda 10.1

## Installation
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Create and activate Python environment
conda create -n dde-table python=3.9
conda init bash
conda activate dde-table

# Install dependencies
conda install -y pytorch==1.10.1 torchvision==0.11.2 torchaudio==0.10.1 cudatoolkit=11.3 cudnn -c pytorch -c conda-forge
python -m pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html
pip install pdfminer.six xlwt xlrd fitz pdf2image tqdm PyMuPDF opencv-python PyPDF2 pdfplumber
conda install -y -c conda-forge poppler

pip install requirements.txt


