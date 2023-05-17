# import importlib
# import pkgutil
#
#
# for _, name, is_pkg in pkgutil.iter_modules(path=__path__):
#     if is_pkg:
#         module = f'{__name__}.{name}'
#         importlib.import_module(module)

from . import pdf  # text image
from . import table  # 表格框线和内容
from . import task_test
