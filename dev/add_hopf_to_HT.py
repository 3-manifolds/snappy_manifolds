"""
HTLinkExteriors is missing the Hopf link.
"""

import snappy
import csv, os, glob

infile = open('../manifold_src/original_manifold_sources/HT_links.csv',
              newline='')
outfile = open('HT_links.csv', 'w', newline='')
csv_in = csv.reader(infile)
csv_out = csv.writer(outfile, lineterminator=os.linesep)

csv_out.writerow(next(csv_in))
csv_out.writerow([1, 'K2a1', 2,'bbaaba.10', 2, [], 0.0, 'None', 3,
                  '48fdc64e88d2062290433d68528931d6', 'dLQacccbjkg_BBdefBBa'])
for row in csv_in:
    row[0] = int(row[0]) + 1
    csv_out.writerow(row)
outfile.close()

