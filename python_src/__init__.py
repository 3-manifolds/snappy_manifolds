__version__ = '1.2.1'

def version():
    return __version__

from .database import get_tables, get_DT_tables, manifolds_path
