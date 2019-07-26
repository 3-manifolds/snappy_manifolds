import snappy
import snappy_manifolds
from snappy.decorated_isosig import *
from itertools import permutations, product

import sys
sys.path.append('../validation')
from compare_common import same_labeled_triangulation_and_peripheral_curves as same

#tables = snappy_manifolds.get_tables(snappy.Manifold,
#                                     snappy.database.IsosigManifoldTable)

def fix_table(new_table, snappy_name):
    name = repr(new_table).split(' ')[0][5:]
    fixed_file = open(name+'fixed2.txt','w')
    notfixed_file = open(name+'notfixed2.txt','w')

    name = name.replace('Table', 'Exteriors')
    old_table = getattr(snappy, snappy_name)
    conn2 = new_table._connection2
    c = conn2.cursor()
    for M_new in new_table:
        print(M_new.name())
        id, isosig = c.execute("SELECT id,triangulation FROM {} WHERE name='{}'".format(new_table._table,M_new.name())).fetchall()[0]
        M_old = old_table[M_new.name()]
        if M_new.num_cusps()>4:
            print('Skipped: '+M_new.name())
            notfixed_file.write(str(id)+','+M_new.name()+'\n')
            continue
        if same(M_new, M_old):
            assert same(snappy.Manifold(isosig),M_old)
            fixed_file.write(str(id)+','+M_new.name()+','+isosig+'\n')
        else:
            try:
                matching_iso = search_for_peripheral_match2(isosig,M_old)
            except ValueError:
                print("Klein thing")
                notfixed_file.write(str(id)+','+M_new.name()+'\n')
                continue
            if matching_iso:
                assert same(snappy.Manifold(matching_iso),M_old)
                fixed_file.write(str(id)+','+M_new.name()+','+matching_iso+'\n')
            else:
                print('No match found: '+ M_new.name())
                notfixed_file.write(str(id)+','+M_new.name()+'\n')
    fixed_file.close()
    notfixed_file.close()

def search_for_peripheral_match2(start_isosig, standard_manifold):
    n = standard_manifold.num_cusps()
    base = start_isosig.split('_')[0]
    decs = all_peripherals_encoded(standard_manifold, start_isosig, snappy.Triangulation)
    for i,dec in enumerate(decs[::-1]):
        print("{}/{}".format(i,len(decs)))
        switched = all_switched_peripheral_signs(dec,n)
        print("number to check: {}".format(len(switched)))
        for k,iso in reversed(list(enumerate(switched))):
            if k % (float(len(switched))/100) == 0:
                print(float(k)/len(switched) * 100)
            M = snappy.Manifold(iso)
            if same(M,standard_manifold):
                return iso
    return None

def search_for_peripheral_match(start_isosig, standard_manifold):
    n = standard_manifold.num_cusps()
    base = start_isosig.split('_')[0]
    decs = [base+'_'+l[0] for l in all_peripherals_encoded(standard_manifold, start_isosig, snappy.Triangulation)]
    all_decorated_isos = set([iso  for dec in decs for iso in all_switched_peripheral_signs(dec,n)])
    for iso in all_decorated_isos:
        if same(snappy.Manifold(iso),standard_manifold):
            return iso
    print('no match found')
    return None

def switch_peripheral_sign(isosig, num_cusps):
    tet, dec = isosig.split('_')
    n = num_cusps
    switched = []
    decoded = decode_integer_list(dec)
    if len(decoded) == 4*n:
        switched = [-x for x in decoded]
    else:
        assert len(decoded) == 5*n
        switched = decoded[:n]
        switched.extend( [-x for x in decoded[n:] ] )
    new_dec = encode_integer_list(switched)
    return tet+'_'+new_dec

def all_switched_peripheral_signs(isosig, num_cusps):
    tet, dec = isosig.split('_')
    n = num_cusps
    switched = []
    decoded = decode_integer_list(dec)
    if len(decoded) == 5*n:
        decoded = decoded[n:]
    isosigs = []
    for signs in product([-1,1],repeat=n):
        switched_decoded = [signs[int(i/4)]*x for i,x in enumerate(decoded)]
        for perm in permutations(range(n)):
            perm = list(perm)
            if perm == range(n): #identity permutation
                perm = []
            perm.extend(switched_decoded)
            new_dec = encode_integer_list(perm)
            isosigs.append(tet+'_'+new_dec)
    return isosigs

def all_switched_peripheral_signs2(isosig, num_cusps):
    tet, dec = isosig.split('_')
    n = num_cusps
    switched = []
    decoded = decode_integer_list(dec)
    if len(decoded) == 5*n:
        decoded = decoded[n:]
    isosigs = []
    for signs in product([-1,1],repeat=n):
        switched_decoded = [signs[int(i/4)]*x for i,x in enumerate(decoded)]
        
        for perm in permutations(range(n)):
            perm = list(perm)
            if perm == range(n): #identity permutation
                perm = []
            perm.extend(switched_decoded)
            new_dec = encode_integer_list(perm)
            isosigs.append(tet+'_'+new_dec)
    return isosigs

def all_peripherals_encoded(manifold, isosig, triangulation_class,
                     ignore_cusp_ordering = False,
                     ignore_curve_orientations = False):

    N = triangulation_class(isosig, remove_finite_vertices = False)
    N.set_peripheral_curves('combinatorial')

    # in Python3 range is an iterator
    trivial_perm = list(range(manifold.num_cusps()))
    
    min_encoded = None
    min_perm = None
    min_flips = None
    peripherals = []
    # Try all combinatorial isomorphisms
    for tri_iso in manifold.isomorphisms_to(N):

        # Permutation of cusps
        perm = inverse_perm(tri_iso.cusp_images())

        if ignore_cusp_ordering:
            # If we do not include the permutation in the encoding,
            # we need to apply it to the matrices
            matrices = [ tri_iso.cusp_maps()[i] for i in perm ]
        else:
            matrices = tri_iso.cusp_maps()

        if ignore_curve_orientations:
            # Determine the multipliers for the columns of the matrices
            # to bring them into canonical form if so desired
            flips = determine_flips(matrices, manifold.is_orientable())
        else:
            flips = [ (1,1) for matrix in matrices ]

        # Encode the matrices
        decorations = pack_matrices_applying_flips(matrices, flips)

        if perm == trivial_perm or ignore_cusp_ordering:
            # Only encode matrices
            encoded = encode_integer_list(decorations)
        else:
            # Encode permutation and matrices
            encoded = encode_integer_list(perm + decorations)

        peripherals.append( (encoded, perm, flips) )

    base = isosig.split('_')[0]
    decs = [base+'_'+l[0] for l in peripherals]
    return decs


#fix_table(tables[0], 'OrientableCuspedCensus')
#fix_table(tables[1], 'NonorientableCuspedCensus')
#fix_table(tables[4], 'LinkExteriors')
#fix_table(tables[5], 'CensusKnots')
#fix_table(tables[6](filter="id>174885"), 'HTLinkExteriors')
"""
limit = 1
T = tables[6]
conn = T._connection2
c = conn.cursor()

i = 0

f = open("HTLinkTablenotfixed.txt","r")
g = open("HTLinkTableextra.txt","a")
h = open("HTLinkTablestillnotfixed.txt","a")
for line in f:
    print(i)
    i += 1
    if i > limit: break
    id, name = line.strip().split(',')
    print(id,name)
    M = snappy.Manifold(name)
    isosig = c.execute("SELECT triangulation FROM {} WHERE name='{}'".format(T._table,name)).fetchall()[0][0]
    matching_iso = search_for_peripheral_match2(isosig,M)
    if matching_iso:
        g.write(str(id)+','+name+','+matching_iso+'\n')
    else:
        h.write(str(id)+','+name+'\n')
f.close()
g.close()
h.close()
"""

"""
f = open('RolfsenTablefixed.txt','r')
g = open('RolfsenTableextra.txt','r')
h = open('RolfsenTablefixeddecorations.txt','w')
lines = f.readlines()
lines.extend(g.readlines())
lines.sort(key=lambda x: int(x.split(',')[0]))
h.writelines(lines)
f.close()
g.close()
h.close()
"""
