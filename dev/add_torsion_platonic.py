""" 
Add torsion fields to platonic manifolds in the interests of
consistency.
"""

import snappy
import csv, os, glob

def torsion(row, tri_index):
    M = snappy.Manifold(row[tri_index])
    tor = [c for c in M.homology().elementary_divisors() if c != 0]
    row.insert(4, repr(tor))

def fix_platonic_torsion_field(file):
    infile = open(
        '../manifold_src/original_manifold_sources/platonic_manifolds/'
        + file, newline='')
    outfile = open(file, 'w', newline='')
    out = csv.writer(outfile, lineterminator=os.linesep)
    for row in csv.reader(infile):
        if row[0] == 'id':
            tri_index = row.index('triangulation')
            row.insert(4, 'torsion')
        else:
            torsion(row, tri_index)
        out.writerow(row)
    outfile.close()

def fix_all_platonic():
    for file in glob.glob(
            '../manifold_src/original_manifold_sources/platonic_manifolds/*.csv'):
        file = os.path.basename(file)
        print('Starting ' + file + '...')
        fix_platonic_torsion_field(file)
        print('    Finished.\n')

fix_all_platonic()


