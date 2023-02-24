from tablefusion_async import crud


def table_overlap(
        outline1: crud.table.TableOutline,
        outline2: crud.table.TableOutline,
) -> bool:
    return (outline1.page != outline2.page
            or outline1.x1 >= outline2.x2 or outline2.x1 >= outline1.x2
            or outline1.y1 >= outline2.y2 or outline2.y1 >= outline1.y2)
