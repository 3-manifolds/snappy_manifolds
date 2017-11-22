import os, sys, time
import sqlite3
import binascii
import re
import csv

"""
This file contains the functions used to pull the data
from the Manifold censuses in csv format to build sqlite
 databases for use by snappy. The first line of the csv
names the columns.
"""

csv_dir = 'original_manifold_sources'

schema_types = {
    'id': 'int',
    'name': 'text',
    'cusps': 'int',
    'betti': 'int',
    'torsion': 'text',
    'volume': 'real',
    'chernsimons': 'real',
    'tets': 'int', 
    'hash': 'text',
    'triangulation': 'text',
    'm': 'int',
    'l': 'int',
    'cusped': 'text',
    'DT': 'text',
    'perm':'int',
    'cuspedtriangulation':'text',
    'solids': 'int',
    'isAugKTG': 'int'
}


def make_table(connection, tablecsv, sub_dir = '', name_index=True):
    """
    Given a csv of manifolds data and a connection to a sqlite database,
    insert the data into a new table. If the csv file is in a subdirectory
    of the csv directory csv_dir, it is given by sub_dir.
    """
    tablename = tablecsv.split('.')[0]
    csv_path = os.path.join(csv_dir, sub_dir, tablecsv)
    csv_file = open(csv_path, 'r')
    csv_reader = csv.reader(csv_file)
        
    #first line is column names
    columns = next(csv_reader)
    schema ="CREATE TABLE %s (id integer primary key"%tablename

    for column in columns[1:]: #first column is always id
        schema += ",%s %s" % (column,schema_types[column])
    schema += ")"
    print('creating ' + tablename)
    connection.execute(schema)
    connection.commit()
    
    insert_query = "insert into %s ("%tablename
    for column in columns[1:len(columns)]:
        insert_query += "%s, " %column
    insert_query = insert_query[:len(insert_query)-2] #one comma too many
    insert_query += ') values ('
    for column in columns[1:len(columns)]:
        if schema_types[column] == 'text':
            insert_query += "'%s', "
        else:
            insert_query += "%s, "
    insert_query = insert_query[:len(insert_query)-2] #one comma too many
    insert_query += ')'
    #print(insert_query)

    for row in csv_reader:
        #print(row)
        data_list = row[1:] #skip id
        for i,data in enumerate(data_list): #chernsimons is None sometimes
            if data == 'None':
                data_list[i] = 'Null'
                #print('Null values found')
                #print(data_list)
        connection.execute(insert_query%tuple(data_list))

    # We need to index columns that will be queried frequently for speed.

    indices = ['hash', 'volume']
    if name_index:
        indices += ['name']
    for column in indices:
        connection.execute(
            'create index %s_by_%s on %s (%s)'%
            (tablename, column, tablename, column))
    connection.commit()
            
def is_stale(dbfile, sourceinfo):
    if not os.path.exists(dbfile):
        return True
    dbmodtime = os.path.getmtime(dbfile)
    for csv_file in sourceinfo:
        csv_path = os.path.join(csv_dir, sourceinfo[csv_file].get('sub_dir', ''), csv_file)
        if os.path.getmtime(csv_path) > dbmodtime:
            return True
    return False
    
if __name__ == '__main__':
    manifold_db = 'manifolds.sqlite'
    manifold_data = {
        'orientable_cusped_census.csv': {},
        'nonorientable_cusped_census.csv': {},
        'orientable_closed_census.csv': {'name_index': False},
        'nonorientable_closed_census.csv': {'name_index': False},
        'census_knots.csv': {},
        'link_exteriors.csv': {}
    }
    if is_stale(manifold_db, manifold_data):
        if os.path.exists(manifold_db):
            os.remove(manifold_db)
        with sqlite3.connect(manifold_db) as connection:
            for file, args in manifold_data.items():
                make_table(connection, file, **args)
            # There are two reasons for using views.  One is that views
            # are read-only, so we have less chance of deleting our data.
            # The second is that they allow joins to be treated as if they
            # were tables, which we need for the closed census.
            connection.execute("""create view orientable_cusped_view as
            select * from orientable_cusped_census""")
            connection.execute("""create view link_exteriors_view as
            select * from link_exteriors""")
            connection.execute("""create view census_knots_view as
            select * from census_knots""")
            connection.execute("""create view nonorientable_cusped_view as
            select * from nonorientable_cusped_census""")
            connection.execute("""create view orientable_closed_view as
            select a.id, b.name, a.m, a.l, a.cusps, a.betti, a.torsion, a.volume,
            a.chernsimons, a.hash, b.triangulation
            from orientable_closed_census a
            left join orientable_cusped_census b
            on a.cusped=b.name""")
            connection.execute("""create view nonorientable_closed_view as
            select a.id, b.name, a.m, a.l, a.cusps, a.betti, a.torsion, a.volume,
            a.hash, b.triangulation
            from nonorientable_closed_census a
            left join nonorientable_cusped_census b
            on a.cusped=b.name""")

    more_db = 'more_manifolds.sqlite'
    more_data = {'HT_links.csv': {}}
    if is_stale(more_db, more_data):
        if os.path.exists(more_db):
            os.remove(more_db)
        with sqlite3.connect(more_db) as connection:
            for file, args in more_data.items():
                make_table(connection, file, **args)
            connection.execute(""" create view HT_links_view as select * from HT_links""")

    platonic_db = 'platonic_manifolds.sqlite'
    platonic_data = {
        'cubical_nonorientable_closed_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'dodecahedral_nonorientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'octahedral_nonorientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'cubical_nonorientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'dodecahedral_orientable_closed_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'octahedral_orientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'cubical_orientable_closed_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'dodecahedral_orientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'cubical_orientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'icosahedral_nonorientable_closed_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'tetrahedral_nonorientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'dodecahedral_nonorientable_closed_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'icosahedral_orientable_closed_census.csv': {'sub_dir': 'platonic_manifolds/'},
        'tetrahedral_orientable_cusped_census.csv': {'sub_dir': 'platonic_manifolds/'},
    }
    if is_stale(platonic_db, platonic_data):
        if os.path.exists(platonic_db):
            os.remove(platonic_db)
        with sqlite3.connect(platonic_db) as connection:
            for file, args in platonic_data.items():
                make_table(connection, file, **args)
