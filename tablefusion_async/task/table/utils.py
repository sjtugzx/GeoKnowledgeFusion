from tablefusion_async import crud
import PyPDF2


def table_overlap(
        outline1: crud.table.TableOutline,
        outline2: crud.table.TableOutline,
) -> bool:
    return (outline1.page != outline2.page
            or outline1.x1 >= outline2.x2 or outline2.x1 >= outline1.x2
            or outline1.y1 >= outline2.y2 or outline2.y1 >= outline1.y2)


# todo: 判断pdf是否存在表格 paper_list 表添加一列
def check_table_exists(file):
    reader = PyPDF2.PdfReader(file)
    num_pages = len(reader.pages)
    for page_number in range(num_pages):
            page = reader.pages[page_number]
            text = page.extract_text()

            # Replace this with your table detection logic
            if 'Table' in text:
                return True
    return False
