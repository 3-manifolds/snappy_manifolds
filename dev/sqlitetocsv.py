import sqlite3
from snappy.db_utilities import decode_torsion


"""
conn = sqlite3.connect("manifolds.sqlite")
c = conn.cursor()

tablename = 'orientable_cusped_census'
#(\n id integer primary key,\n name text,\n cusps int,\n perm int,\n betti int,\n torsion blob,\n volume real,\n chernsimons real,\n tets int, \n hash blob,\n triangulation blob)

f = open('orientable_cusped_census.csv','w')
for line in c.execute("SELECT * FROM orientable_cusped_census"):
    line = list(line)
    line[5] = decode_torsion(str(line[5]))
    line[9] = str(line[9]).encode('hex')
    line.pop(10)
    f.write('{},{},{},{},{},{},{},{},{},{}\n'.format(*line))
f.close()

tablename = 'census_knots'
# (\n id integer primary key,\n name text,\n cusps int,\n perm int,\n betti int,\n torsion blob,\n volume real,\n chernsimons real,\n tets int, \n hash blob,\n triangulation blob)')
f = open('census_knots.csv','w')
for line in c.execute("SELECT * FROM census_knots"):
    line = list(line)
    line[5] = decode_torsion(str(line[5]))
    line[9] = str(line[9]).encode('hex')
    line.pop(10)
    f.write('{},{},{},{},{},{},{},{},{},{}\n'.format(*line))
f.close()


tablename = 'link_exteriors'
#(\n id integer primary key,\n name text,\n cusps int,\n perm int,\n DT text,\n betti int,\n torsion blob,\n volume real,\n chernsimons real,\n tets int, \n hash blob,\n triangulation blob)')
f = open('link_exteriors.csv','w')
for line in c.execute("SELECT * FROM link_exteriors"):
    line = list(line)
    line[6] = decode_torsion(str(line[6]))
    line[10] = str(line[10]).encode('hex')
    line.pop(11)
    f.write('{},{},{},{},{},{},{},{},{},{},{}\n'.format(*line))
f.close()


tablename = 'orientable_closed_census'
#(\n id integer primary key,\n cusped text,\n m int,\n l int,\n betti int,\n torsion blob,\n volume real,\n chernsimons real,\n hash blob\n)')
f = open('orientable_closed_census.csv','w')
for line in c.execute("SELECT * FROM orientable_closed_census"):
    line = list(line)
    line[5] = decode_torsion(str(line[5]))
    line[8] = str(line[8]).encode('hex')
    f.write('{},{},{},{},{},{},{},{},{}\n'.format(*line))
f.close()


tablename = 'nonorientable_cusped_census'
#(\n id integer primary key,\n name text,\n cusps int,\n perm int,\n betti int,\n torsion blob,\n volume real,\n tets int, \n hash blob,\n triangulation blob)')
f = open('nonorientable_cusped_census.csv','w')
for line in c.execute("SELECT * FROM nonorientable_cusped_census"):
    line = list(line)
    line[5] = decode_torsion(str(line[5]))
    line[8] = str(line[8]).encode('hex')
    line.pop(9)
    f.write('{},{},{},{},{},{},{},{},{}\n'.format(*line))
f.close()


tablename = 'nonorientable_closed_census'
#(\n id integer primary key,\n cusped text,\n m int,\n l int,\n betti int,\n torsion blob,\n volume real,\n hash blob\n)')
f = open('nonorientable_closed_census.csv','w')
for line in c.execute("SELECT * FROM nonorientable_closed_census"):
    line = list(line)
    line[5] = decode_torsion(str(line[5]))
    line[7] = str(line[7]).encode('hex')
    f.write('{},{},{},{},{},{},{},{}\n'.format(*line))
f.close()


conn2 = sqlite3.connect('more_manifolds.sqlite')
c2 = conn2.cursor()
tablename = 'HT_links'
#(\n id integer primary key,\n name text,\n cusps int,\n perm int,\n DT text,\n betti int,\n torsion blob,\n volume real,\n chernsimons real,\n tets int, \n hash blob,\n triangulation blob)
f = open('HT_links.csv','w')
for line in c2.execute("SELECT * FROM HT_links"):
    line = list(line)
    line[6] = decode_torsion(str(line[6]))
    line[10] = str(line[10]).encode('hex')
    line.pop(11)
    f.write('{},{},{},{},{},{},{},{},{},{},{}\n'.format(*line))
f.close()
"""
conn3 = sqlite3.connect('platonic_manifolds.sqlite')
c3 = conn3.cursor()
platonic_tables = [l[0] for l in c3.execute("SELECT name FROM sqlite_master where type='table'").fetchall()]

for tablename in platonic_tables:
    f = open(tablename+'.csv','w')
    if tablename in ['dodecahedral_nonorientable_cusped_census',
                     'octahedral_nonorientable_cusped_census']:
        columns = ['id',
                   'name',
                   'perm',
                   'cusps',
                   'betti',
                   'tets',
                   'solids',
                   'hash',
                   'volume',
                   'triangulation']
        columns.pop(2)
        f.write(','.join(columns)+'\n')
        for line in c3.execute("SELECT * FROM " + tablename):
            line = list(line)
            line.pop(2)
            line[6] = str(line[6]).encode('hex')
            f.write('{},{},{},{},{},{},{},{},{}\n'.format(*line))
        f.close()
    elif tablename == 'octahedral_orientable_cusped_census':
        columns = ['id',
                   'name',
                   'cusps',
                   'betti',
                   'tets',
                   'solids',
                   'hash',
                   'volume',
                   'triangulation',
                   'DT',
                   'isAugKTG']
        f.write(','.join(columns)+'\n')
        for line in c3.execute("SELECT * FROM " + tablename):
            line = list(line)
            line[6] = str(line[6]).encode('hex')
            f.write('{},{},{},{},{},{},{},{},{},{},{}\n'.format(*line))
        f.close()
    else:
        columns = ['id',
                   'name',
                   'cusps',
                   'betti',
                   'tets',
                   'solids',
                   'hash',
                   'volume',
                   'triangulation']
        f.write(','.join(columns)+'\n')
        for line in c3.execute("SELECT * FROM " + tablename):
            line = list(line)
            line[6] = str(line[6]).encode('hex')
            f.write('{},{},{},{},{},{},{},{},{}\n'.format(*line))
        f.close()
