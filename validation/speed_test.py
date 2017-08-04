import snappy_manifolds
import snappy
import snappy.database_old
import time

snappy.database_old.Manifold = snappy.Manifold

tables = snappy_manifolds.get_tables(snappy.database.ManifoldTable)

def time_one_table(table):
    print('Timings for %s' % table)
    
    start_time = time.time()
    names = []
    manifolds = []
    for M in table:
        M.volume()
        names.append(M.name())
        manifolds.append(M)
    stop_time = time.time()
    print(4*' ' + 'Basic interation: %.1f sec' % (stop_time - start_time))

    start_time = time.time()
    for name in names:
        table[name].volume()
    stop_time = time.time()
    print(4*' ' + 'Lookup by name: %.1f sec' % (stop_time - start_time))
        
    #start_time = time.time()
    #for M in manifolds:
    #    table.identify(M)
    #stop_time = time.time()
    #dprint(4*' ' + 'Identify: %.1f sec' % (stop_time - start_time))
        

def time_table(new_table, tablename):
    name = repr(new_table).split(' ')[0][5:]
    name = name.replace('Table', 'Census')
    old_table = getattr(snappy, tablename)
    for M_new in new_table:
        M_old = old_table[M_new.name()]
        if not same(M_new, M_old):
            print(M_new.name())
    
#check_table(tables[0],'OrientableCuspedCensus')
#check_table(tables[1],'NonorientableCuspedCensus')
#check_table(tables[4],'LinkExteriors')
#check_table(tables[5],'CensusKnots')
#check_table(tables[6],'HTLinkExteriors')


time_one_table(snappy.database_old.OrientableCuspedCensus)
time_one_table(tables[0])


#time_one_table(snappy.HTLinkExteriors)
#time_one_table(tables[6])
