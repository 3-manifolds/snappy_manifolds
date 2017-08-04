"""
Putting geometrically natural peripheral framings on the Platonic
cusped manifolds.

Initially, the plan was to sort by the cusps by cusp volume, but
SnapPy was struggling with that computation in some of the larger
examples.

In the end, we simply installed a shortest framing on each cusp and
called it a day.
"""

import snappy
import glob, os
import pandas as pd
platonic_dir = '../manifold_src/original_manifold_sources/platonic_manifolds/'
platonic_files = glob.glob(platonic_dir + '*_cusped_census.csv')


def cusp_volumes(manifold):
    """
    >>> M = snappy.Manifold('L14n62484')
    >>> ['%.5f' % vol for vol in cusp_volumes(M)]
    ['5.13747', '7.53894', '5.68026', '4.65875']
    """
    M = manifold
    vols = []
    for i in range(M.num_cusps()):
        nb = M.cusp_neighborhood()
        stop = nb.stopping_displacement(i)
        nb.set_displacement(stop, i)
        vols.append(nb.volume(i))
    return vols

def order_cusps_by_volume(isosig):
    """
    >>> iso = 'AvLLvLPAQLPAvPMPMQcddihkihlonppnopuvwuuxyyzxzzrwrgvgrfeumieuaamtcslhlulco'
    >>> M = snappy.Manifold(iso)
    >>> ['%.5f' % vol for vol in cusp_volumes(M)]
    ['4.33013', '6.92820', '5.19615', '13.85641']
    >>> new_iso = order_cusps_by_volume(iso); new_iso
    'AvLLvLPAQLPAvPMPMQcddihkihlonppnopuvwuuxyyzxzzrwrgvgrfeumieuaamtcslhlulco_acbdaBbBabBbBbBaBbBa'
    >>> N = snappy.Manifold(new_iso)
    >>> ['%.5f' % vol for vol in cusp_volumes(N)]
    ['4.33013', '5.19615', '6.92820', '13.85641']
    """
    try:
        M = snappy.ManifoldHP(isosig)
        n = M.num_cusps()
        vols = [(float(vol), i) for i, vol in enumerate(cusp_volumes(M))]
        vols.sort()
        perm = {i:j for j, (v, i) in enumerate(vols)}
        M._reindex_cusps([perm[i] for i in range(n)])
        M.set_peripheral_curves('shortest')
        new_vols = [float(vol) for vol in cusp_volumes(M)]
        assert new_vols == sorted(new_vols)
        return M.triangulation_isosig()
    except:
        print('Problem with %s' % isosig)
        return isosig + '___'

def decorate_by_shortest(isosig):
    """
    Add the decoration to the isosig corresponding to a shortest
    peripheral framing.
    """
    M = snappy.ManifoldHP(isosig)
    M.set_peripheral_curves('shortest')
    return M.triangulation_isosig()

def update_file(file_name):
    basename = os.path.basename(file_name)
    print('Starting ' + basename)
    census = pd.read_csv(file_name)
    census['triangulation'] = census['triangulation'].apply(decorate_by_shortest)
    census.to_csv(basename, index=False)
    print('Finished ' + basename)
    return census

def nice_volume(isosig):
    M = snappy.ManifoldHP(isosig)
    return float(M.volume())

def update_volume(file_name):
    basename = os.path.basename(file_name)
    print('Starting ' + basename)
    census = pd.read_csv(file_name)
    census['volume'] = census['triangulation'].apply(nice_volume)
    census.to_csv(basename, index=False)
    print('Finished ' + basename)
    return census

if __name__ == '__main__':
    import doctest
    import multiprocessing
    pool = multiprocessing.Pool(12)
    #M = snappy.ManifoldHP('kvvLQQMkghifhifgjjjmtmiutlpmta')
    #doctest.testmod()
    #df = update_volume(platonic_dir + 'dodecahedral_orientable_cusped_census.csv')
    pool.map(update_volume, platonic_files)
