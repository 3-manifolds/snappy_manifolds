import snappy_manifolds
import snappy
import snappy.database
import snappy.database_old
from collections import OrderedDict
from compare_common import same_labeled_triangulation_and_peripheral_curves as same

snappy.database_old.Manifold = snappy.Manifold


def name(some_object):
    return some_object.__class__.__name__

new_tables = OrderedDict((name(table),table) for table in
                         snappy_manifolds.get_tables(snappy.database.ManifoldTable))


def check_table(table_name):
    new_table = new_tables[table_name]
    old_table = getattr(snappy.database_old, table_name)
    print('Starting to check ' + table_name + '...')
    if table_name == 'OrientableClosedCensus':
        assert len(new_table) == len(old_table)
        for i, M_new in enumerate(new_table):
            M_old = old_table[i]
            if not same(M_new, M_old):
                print('Difference with %s' % M_new)
    else:
        for M_new in new_table:
            M_old = old_table[M_new.name()]
            if not same(M_new, M_old):
                 print('Difference with %s' % M_new)
    print('Finished checking ' + table_name + '.')


if __name__ == '__main__':
    import multiprocessing
    n = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(n)
    print('Current tables:')
    for table in new_tables.values():
        print('  ' + name(table))
        table.random()

    print('\nBeginning comparison of new with old in %d processes' % n)
    pool.map(check_table, new_tables.keys())
