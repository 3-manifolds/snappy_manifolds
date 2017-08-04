import snappy, csv
from compare_common import same_labeled_triangulation_and_peripheral_curves

def test_new_census(census, max_errors=20):
    file = open('../manifold_src/' + census + '.csv')
    data = csv.DictReader(file)
    errors = 0
    for row in data:
        M_old = snappy.Triangulation(row['name'])
        M_new = snappy.Triangulation(row['triangulation'])
        M_new.set_name(row['name'])
        if not same_labeled_triangulation_and_peripheral_curves(M_old, M_new):
            print(row['name'], row['triangulation'])
            errors += 1
            if errors >= max_errors:
                break
    
#---------- test fix ----------

import multiprocessing

def check_row(row):
    same = same_labeled_triangulation_and_peripheral_curves
    M_old = snappy.Manifold(row['name'])
    M_new = snappy.Manifold(row['triangulation'])
    if M_old.num_cusps() == 1:
        if not same(M_old, M_new):
            M_new.set_peripheral_curves([[[-1, 0], [0, -1]]])
            if not same(M_new, M_old):
                print(row['name'], row['triangulation'])

def test_fix(census):
    file = open('../manifold_src/' + census + '.csv')
    data = list(csv.DictReader(file))
    procs = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(procs)
    pool.map(check_row, data)
