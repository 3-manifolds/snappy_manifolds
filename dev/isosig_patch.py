import snappy
from snappy.decorated_isosig import *

def _gluing_data(self):
    s = self._to_string()
    gluings = []
    permutations = []
    for i, block in enumerate(s.split('\n\n')[2:-1]):
        block = block.split('\n')
        if i == 0:
            gluings.append(block[1].split())
            permutations.append(block[2].split())
        else:
            gluings.append(block[0].split())
            permutations.append(block[1].split())
    return gluings, permutations

    

snappy.Manifold._gluing_data = _gluing_data


def start_tet_and_perm(M, decorated=True):
    """
    Starting with a Manifold from database, find all possible starting
    tetrahedra and labelings of that tetrahedron that results in an isosig
    giving the exact same triangulation (i.e. _gluing_data) as the original
    when constructed by snappy.Manifold
    """
    s = M.name()
    original_gluing_data = M._gluing_data()
    seen_isosigs = set()
    for i in range(M.num_tetrahedra()):
        for j in range(24):
            isosig = snappy.Manifold(s)._permutation_isosig_orientation_preserving(i,j, decorated=decorated)
            if isosig not in seen_isosigs:
                if snappy.Manifold(isosig)._gluing_data() == original_gluing_data:
                    return isosig
                seen_isosigs.add(isosig)                
    return ''


def all_isosigs(M, decorated=True):
    """
    Starting with a Manifold from database, find all possible starting
    tetrahedra and labelings of that tetrahedron that results in an isosig
    giving the exact same triangulation (i.e. _gluing_data) as the original
    when constructed by snappy.Manifold
    """
    s = M.name()
    original_gluing_data = M._gluing_data()
    seen_isosigs = set()
    for i in range(M.num_tetrahedra()):
        for j in range(24):
            isosig = snappy.Manifold(s)._permutation_isosig(i,j, decorated=decorated)
            if isosig not in seen_isosigs:
                if snappy.Manifold(isosig)._gluing_data() == original_gluing_data:
                    yield isosig
                seen_isosigs.add(isosig)                



"""
census = snappy.NonorientableClosedCensus
f = open('compatible_isosigs_nonorientableclosedcensus.txt','w')
g = open('special_cases_nonorientableclosedcensus.txt', 'w')
i = 0
total = len(census)

for M in census():
    print(i, float(i)/total)
    m,l = M.cusp_info()[0]['filling']
    m, l = int(round(m)), int(round(l))
    isosig = start_tet_and_perm(M, decorated=True)
    if len(isosig) == 0:
        g.write(M.name()+','+str(m)+','+str(l)+'\n')
    else:
        f.write(M.name()+','+str(m)+','+str(l)+' '+start_tet_and_perm(M)+'\n')
    i += 1
f.close()
g.close()



census = snappy.HTLinkExteriors
f = open('compatible_isosigs_htlinkexteriors3.txt','w')
g = open('special_cases_htlinkexteriors3.txt', 'w')
i = 0
total = len(census)

for M in census():
    print(i, float(i)/total)
    isosig = start_tet_and_perm(M, decorated=False)
    if len(isosig) == 0:
        g.write(M.name()+'\n')
    else:
        f.write(M.name()+' '+start_tet_and_perm(M)+'\n')
    i += 1
f.close()
g.close()

"""
"""
Picking lex first framing, which might reverse orientation.
Look at all valid decorations, not just lex first. Find lex first one which
preserves orientation (has determinant 1).
decorated_isosig in decorated_isosig.py
"""

"""

"""
