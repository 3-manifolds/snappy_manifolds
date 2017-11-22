"""
We do only a very basic test for this module, since most of the
doctests are run by snappy.

>>> Rolfsen, HT = get_DT_tables()
>>> len(Rolfsen), len(HT)
(1215, 180510)
>>> str(HT['L12n345'])
'lbbjceGkjHILFadb.010001100011'
"""

from .database import get_DT_tables
import sys
import doctest
this_module = sys.modules[__name__]

def run_tests():
    result = doctest.testmod(this_module)
    print('snappy_manifolds: ' + repr(result))

if __name__ == '__main__':
    run_tests()
