from tablefusion_async import crud
import fitz  # PyMuPDF


def table_overlap(
        outline1: crud.table.TableOutline,
        outline2: crud.table.TableOutline,
) -> bool:
    return (outline1.page != outline2.page
            or outline1.x1 >= outline2.x2 or outline2.x1 >= outline1.x2
            or outline1.y1 >= outline2.y2 or outline2.y1 >= outline1.y2)


# 判断pdf是否存在表格 paper_list 表添加一列
def check_table_exists(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = doc.page_count

    for page_number in range(num_pages):
        page = doc.load_page(page_number)
        text = page.get_text()
        # print("page: ", page, text)
        # Replace this with your table detection logic
        if 'Table' in text:
            return True
        image_list = page.get_images()
        for image_index, image in enumerate(image_list, start=1):
            if is_table_image(image):
                return True

    return False


def is_table_image(image):
    # Replace this with your table detection logic using image processing
    # You can use techniques like template matching, contour detection, etc.
    # Example: Check if the image has a certain size or aspect ratio
    width = image["width"]
    height = image["height"]
    if width > 100 and height > 100:
        return True

    return False

# def check_table_exists(pdf_path):
#     with open(pdf_path, 'rb') as file:
#         reader = PyPDF2.PdfFileReader(file)
#         num_pages = reader.numPages
#
#         for page_number in range(num_pages):
#             page = reader.getPage(page_number)
#             text = page.extractText()
#
#             # Replace this with your table detection logic
#             if 'table' in text.lower():
#                 return True
#
#     return False
