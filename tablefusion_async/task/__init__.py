# import importlib
# import pkgutil
#
#
# for _, name, is_pkg in pkgutil.iter_modules(path=__path__):
#     if is_pkg:
#         module = f'{__name__}.{name}'
#         importlib.import_module(module)

from . import pdf
# from . import text
from . import table
