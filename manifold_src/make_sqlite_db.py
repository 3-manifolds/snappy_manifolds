import os, sys, time
import sqlite3
import binascii
import re

"""
This file contains the functions used to pull the data
from the Manifold censuses in csv format to build sqlite
 databases for use by snappy. The first line of the csv
names the columns.
"""


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

cusped_schema ="""
CREATE TABLE %s (
 id integer primary key,
 name text,
 cusps int,
 betti int,
 torsion text,
 volume real,
 chernsimons real,
 tets int, 
 hash text,
 triangulation text)
"""

cusped_insert_query = """insert into %s
(name, cusps, betti, torsion, volume, chernsimons, tets, hash, triangulation)
values ('%s', %s, %s, '%s', %s, %s, %s, '%s', '%s')"""

closed_schema ="""
CREATE TABLE %s (
 id integer primary key,
 cusped text,
 m int,
 l int,
 betti int,
 torsion text,
 volume real,
 chernsimons real,
 hash text
)
"""

closed_insert_query = """insert into %s
(cusped, m, l, betti, torsion, volume, chernsimons, hash)
values ('%s', %d, %d, %d, '%s', %s, %s, '%s')"""

nono_cusped_schema ="""
CREATE TABLE %s (
 id integer primary key,
 name text,
 cusps int,
 betti int,
 torsion text,
 volume real,
 tets int, 
 hash text,
 triangulation text)
"""

nono_cusped_insert_query = """insert into %s
(name, cusps, betti, torsion, volume, tets, hash, triangulation)
values ('%s', %s, %s, '%s', %s, %s, '%s', '%s')"""

nono_closed_schema ="""
CREATE TABLE %s (
 id integer primary key,
 cusped text,
 m int,
 l int,
 betti int,
 torsion text,
 volume real,
 hash text
)
"""

nono_closed_insert_query = """insert into %s
(cusped, m, l, betti, torsion, volume, hash)
values ('%s', %d, %d, %d, '%s', %s, '%s')"""

USE_COBS = 1 << 7
USE_STRING = 1 << 6
epsilon = 0.000001

closed_re = re.compile('(.*)\((.*),(.*)\)')

def create_manifold_tables(connection):
    """
    Create the empty tables for our manifold database.
    """
    for table in ['orientable_cusped_census',
                  'link_exteriors',
                  'census_knots']:
        connection.execute(cusped_schema%table)
        connection.commit()
    for table in ['orientable_closed_census']:
        connection.execute(closed_schema%table)
        connection.commit()
    for table in ['nonorientable_cusped_census']:
        connection.execute(nono_cusped_schema%table)
        connection.commit()
    for table in ['nonorientable_closed_census']:
        connection.execute(nono_closed_schema%table)
        connection.commit()


def insert_closed_manifold(connection, table, mfld):
    """
    Insert a closed manifold into the specified table.
    """
    cusped, m, l = closed_re.match(repr(mfld)).groups()
    homology = mfld.homology()
    betti = homology.betti_number()
    divisors = [x for x in homology.elementary_divisors() if x > 0]
    torsion = binascii.hexlify(encode_torsion(divisors))
    volume = mfld.volume()
    if mfld.is_orientable():
        try:
            chernsimons = mfld.chern_simons()
        except:
            chernsimons = 'NULL'
    hash = db_hash(mfld)
    if mfld.is_orientable():
        query = closed_insert_query%(
            table, cusped, int(m), int(l), int(betti),
            torsion, volume, chernsimons, hash)
    else:
        query = nono_closed_insert_query%(
            table, cusped, int(m), int(l), int(betti),
            torsion, volume, hash)
    connection.execute(query)
    
def insert_cusped_manifold(connection, table, mfld,
                           is_link=False,
                           use_string=False):
    """
    Insert a cusped manifold into the specified table.
    """
    name = mfld.name()
    cusps = mfld.num_cusps()
    homology = mfld.homology()
    betti = homology.betti_number()
    divisors = [x for x in homology.elementary_divisors() if x > 0]
    torsion = binascii.hexlify(encode_torsion(divisors))
    volume = mfld.volume()
    if mfld.is_orientable():
        try:
            cs = mfld.chern_simons()
        except ValueError:
            print('Chern-Simons failed for %s'%name)
            cs = 'NULL'
    tets = mfld.num_tetrahedra()
    use_cobs, triangulation = get_header(mfld, is_link, use_string)
    if use_cobs:
        cobs = mfld.set_peripheral_curves('combinatorial')
        mfld.set_peripheral_curves(cobs) # undo the basis change
        try:
            triangulation += encode_matrices(cobs)
        except OverflowError:
            #fall back to the verbose string record
            header = mfld.num_cusps() | USE_STRING
            triangulation = bytes(bytearray([header]))
            use_string = True
    if use_string:
        triangulation += mfld.without_hyperbolic_structure()._to_string()
    else:
        triangulation += mfld._to_bytes()
    triangulation = binascii.hexlify(triangulation)
    hash = db_hash(mfld)
    if mfld.is_orientable():
        query = cusped_insert_query%(
            table, name, cusps, betti, torsion,
            volume, cs, tets, hash, triangulation)
    else:
        query = nono_cusped_insert_query%(
            table, name, cusps, betti, torsion,
            volume, tets, hash, triangulation)
    connection.execute(query)



def make_table(connection, tablecsv, sub_dir = '', name_index=True):
    """
    Given a csv of manifolds data and a connection to a sqlite database,
    insert the data into a new table. If the csv file is in a subdirectory
    of original_manifold_sources/, it is given by sub_dir.
    """
    tablename = tablecsv.split('.')[0]
    csv = open('original_manifold_sources/'+ sub_dir + tablecsv,'r')
    #first line is column names
    columns = csv.readline().strip().split(',')
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

    for line in csv:
        data_list = extract_data_from_line(line)[1:] #skip id
        for i,data in enumerate(data_list): #chernsimons is None sometimes
            if data == 'None':
                data_list[i] = 'Null'
                #print('Null values found')
                #print(data_list)
        connection.execute(insert_query%tuple(data_list))
    csv.close()

    # This index makes it fast to join this table on its name column.
    # Without the index, the join is very slow.
    if name_index:
        connection.execute(
            'create index %s_by_name on %s (name)'%(tablename,tablename))
    connection.commit()

def extract_data_from_line(s):
    """
    Split a string along the comma char, except for commas between (), [], "",
    or '', and clean up each entry.
    """
    split = []
    substring = []
    is_inside_parens = False
    is_inside_bracs = False
    is_inside_sing_quotes = False
    is_inside_doub_quotes = False
    for c in s:
        substring.append(c)
        if c == ',' and not is_inside_parens and not is_inside_bracs and not is_inside_sing_quotes and not is_inside_doub_quotes:
            split.append(''.join(substring[:-1]).strip())
            substring = []
        if c == '(':
            is_inside_parens = True
        if c == ')' and is_inside_parens:
            is_inside_parens = False
        if c == '[':
            is_inside_bracs = True
        if c == ']' and is_inside_bracs:
            is_inside_bracs = False
        if c == "'":
            if is_inside_sing_quotes:
                is_inside_sing_quotes = False
            else:
                is_inside_sing_quotes = True
        if c == '"':
            if is_inside_doub_quotes:
                is_inside_doub_quotes = False
            else:
                is_inside_doub_quotes = True
    split.append(''.join(substring).strip())
    for i,s in enumerate(split):
        if s[0] == '"' and s[-1] == '"':
            split[i] = s[1:-1]
        if s[0] == "'" and s[-1] == "'":
            split[i] = s[1:-1]
    return split
            
    
def make_orientable_cusped(connection, tablecsv, name_index=True):
    """
    Give a csv file containing data
    """
    tablename = tablecsv.split('.')[0]
    csv = open(tablecsv,'r')
    csv.readline()
    for line in csv:
        s = line.split('"')
        id,name,cusps,perm,betti,blank = s[0].split(',')
        torsion = s[1]
        blank,volume,chernsimons,tets,hash,triangulation = s[2].split(',')
        connection.execute(cusped_insert_query%(tablename, name, cusps, betti, torsion, volume, chernsimons, tets, hash, triangulation))
    csv.close()
    connection.commit()
    # This index makes it fast to join this table on its name column.
    # Without the index, the join is very slow.
    if name_index:
        connection.execute(
            'create index o_cusped_by_name on orientable_cusped_census (name)')


#id,name,cusps,perm,betti,torsion,volume,tets,hash,triangulation

def make_nonorientable_cusped(connection, tablecsv):
    """
    Give a csv file containing data
    """
    tablename = tablecsv.split('.')[0]
    csv = open(tablecsv,'r')
    csv.readline()
    for line in csv:
        s = line.split('"')
        id,name,cusps,perm,betti,blank = s[0].split(',')
        torsion = s[1]
        blank, volume,tets,hash,triangulation = s[2].split(',')
        connection.execute(nono_cusped_insert_query%(tablename,name,cusps,betti,torsion,volume,tets,hash,triangulation))
    csv.close()
    connection.commit()
    # This index makes it fast to join this table on its name column.
    # Without the index, the join is very slow.
    connection.execute(
        'create index o_cusped_by_name on orientable_cusped_census (name)')


def make_links(connection, tablecsv):
    
    
    for n in range(1, 6):
        for M in LinkExteriors(n):
            M.set_name(M.name().split('(')[0])
            insert_cusped_manifold(connection, table, M,
                                   is_link=True)
    connection.commit()

def make_morwen_links(connection):
    table = 'morwen_links'
    for n in range(1, 8):
        m=1
        for M in MorwenLinks(n):
            M.set_name(M.name().split('(')[0])
            print('%s %s %s'%(n, m, M.name()))
            m += 1
            insert_cusped_manifold(connection, table, M,
                                   is_link=True)
    connection.commit()

def make_census_knots(connection):
    table = 'census_knots'
    for M in CensusKnots():
        M.set_name(M.name().split('(')[0])
        insert_cusped_manifold(connection, table, M,
                               is_link=True)
    connection.commit()

def make_closed(connection):
    table = 'orientable_closed_census'
    for M in OrientableClosedCensus():
        insert_closed_manifold(connection, table, M)
    connection.commit()

def make_nono_cusped(connection):
    table = 'nonorientable_cusped_census'
    for M in NonorientableCuspedCensus():
        insert_cusped_manifold(connection, table, M)
    connection.commit()

def make_nono_closed(connection):
    table = 'nonorientable_closed_census'
    for M in NonorientableClosedCensus():
        insert_closed_manifold(connection, table, M)
    connection.commit()

if __name__ == '__main__':
    dbfile = 'manifolds.sqlite'
    if os.path.exists(dbfile):
        os.remove(dbfile)
    connection = sqlite3.connect(dbfile)

    make_table(connection,'orientable_cusped_census.csv')
    make_table(connection,'nonorientable_cusped_census.csv')
    make_table(connection,'orientable_closed_census.csv', name_index=False)
    make_table(connection,'nonorientable_closed_census.csv', name_index=False)
    make_table(connection,'census_knots.csv')
    make_table(connection,'link_exteriors.csv')
        
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
    select a.id, b.name, a.m, a.l, a.betti, a.torsion, a.volume,
    a.chernsimons, a.hash, b.triangulation
    from orientable_closed_census a
    left join orientable_cusped_census b
    on a.cusped=b.name""")
    connection.execute("""create view nonorientable_closed_view as
    select a.id, b.name, a.m, a.l, a.betti, a.torsion, a.volume,
    a.hash, b.triangulation
    from nonorientable_closed_census a
    left join nonorientable_cusped_census b
    on a.cusped=b.name""")
    connection.close()

    dbfile2 = 'more_manifolds.sqlite'
    if os.path.exists(dbfile2):
        os.remove(dbfile2)
    connection2 = sqlite3.connect(dbfile2)

    make_table(connection2,'HT_links.csv')
    connection2.execute(""" create view HT_links_view as select * from HT_links""")
    connection2.close()

    dbfile3 = 'platonic_manifolds.sqlite'
    if os.path.exists(dbfile3):
        os.remove(dbfile3)
    connection3 = sqlite3.connect(dbfile3)
    platonic_csvs = ['cubical_nonorientable_closed_census.csv',
                     'dodecahedral_nonorientable_cusped_census.csv',
                     'octahedral_nonorientable_cusped_census.csv',
                     'cubical_nonorientable_cusped_census.csv',
                     'dodecahedral_orientable_closed_census.csv',
                     'octahedral_orientable_cusped_census.csv',
                     'cubical_orientable_closed_census.csv',
                     'dodecahedral_orientable_cusped_census.csv',
                     'cubical_orientable_cusped_census.csv',
                     'icosahedral_nonorientable_closed_census.csv',
                     'tetrahedral_nonorientable_cusped_census.csv',
                     'dodecahedral_nonorientable_closed_census.csv',
                     'icosahedral_orientable_closed_census.csv',
                     'tetrahedral_orientable_cusped_census.csv']
    for csv in platonic_csvs:
        make_table(connection3,csv, sub_dir = 'platonic_manifolds/')
    connection3.close()
