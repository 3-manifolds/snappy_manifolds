"""
Cusp field currently missing from some closed censuses.  For the
others, the cusp field records the number of cusps in the description
not the number of the filled manifold.

Additionally, the triangulation field of the closed platonic manifolds
was not quoted as it needs to be for a CSV file.
"""

import csv, os, glob

def fix_closed_lacking_cusp_field(file):
    infile = open('../manifold_src/original_manifold_sources/' + file, newline='')
    outfile = open(file, 'w', newline='')
    out = csv.writer(outfile, lineterminator=os.linesep)
    position = 4
    for row in csv.reader(infile):
        if row[0] == 'id':
            row.insert(position, 'cusps')
        else:
            row.insert(position, '0')
        out.writerow(row)
    outfile.close()

fix_closed_lacking_cusp_field('nonorientable_closed_census.csv')
fix_closed_lacking_cusp_field('orientable_closed_census.csv')

def fix_platonic_cusp_field(file):
    infile = open(
        '../manifold_src/original_manifold_sources/platonic_manifolds/'
        + file, newline='')
    outfile = open(file, 'w', newline='')
    out = csv.writer(outfile, lineterminator=os.linesep)
    position = 4
    for row in csv.reader(infile):
        if row[0] != 'id':
            row[2] = 0
            row[-2] += ',' + row[-1]
            row = row[:-1]
        out.writerow(row)
    outfile.close()

def fix_all_platonic():
    for file in glob.glob(
            '../manifold_src/original_manifold_sources/platonic_manifolds/*closed*.csv'):
        fix_platonic_cusp_field(os.path.basename(file))
    
            

fix_all_platonic()
