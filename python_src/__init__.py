__version__ = '0.9.3a1'

def version():
    return __version__

from .database import get_tables, get_DT_tables, manifolds_path
