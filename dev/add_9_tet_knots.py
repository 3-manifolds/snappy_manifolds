"""
There are 1267 exteriors of knots in S^3 in OrientableCuspedCensus.

Based on https://arxiv.org/abs/1307.4439v3 we sort them by

(num_tets, volume, length of the systole, length of second shortest geodesic)

where the first two are sorted in *ascending* order and the second two
in *descending* order.

As is explicit in the above paper, by the length of the second
shortest geodesic, they mean::

  M.dual_curves()[1].complete_length.real()

which sometimes corresponds to a *non-primitive* geodesic and is
triangulation dependent.

For the 9 tet knots, we use the second *primitive* geodesic as the
tiebreaker.  If this was applied uniformly, it would interchange
K8_300 and K8_301.
"""

import pandas as pd
import snappy
import taskdb2
import numpy as np
import fix_decorations

def manifold_data(task):
    M = snappy.ManifoldHP(task['name'])
    s = 0
    spec = []
    while len(spec) < 2:
        s = s + 0.5
        spec = M.length_spectrum(s)
    systole = spec[0].length.real()
    i = 1 if spec[0].multiplicity == 1 else 0
    next = spec[i].length.real()

    task['tets'] = M.num_tetrahedra()
    task['volume'] = float(M.volume())
    task['systole'] = float(systole)
    task['next_shortest'] = float(next)
    task['done'] = True

def manifold_data_alt(task):
    M = snappy.ManifoldHP(task['name'])
    curves = M.dual_curves()
    task['shortest_dual_curve'] = float(curves[0].complete_length.real())
    task['next_dual_curve'] = float(curves[1].complete_length.real())
    task['done'] = True


def initial_data():
    df = pd.read_csv('/home/sage/projects/combined_conjecture/paper/exceptional_census_data/data/exceptional_fillings.csv.bz2')
    df = df[df.kind=='S3'][['cusped', 'slope']].copy()
    return df

def current_name(name):
    M = snappy.Manifold(name)
    return snappy.CensusKnots.identify(M).name()


def load_and_sort():
    db = taskdb2.ExampleDatabase('census_knots')
    df = db.dataframe()
    df['minus_systole'] = -df.systole
    df['minus_next_shortest'] = -df.next_shortest
    df = df.sort_values(['tets', 'volume', 'minus_systole', 'minus_next_shortest'])
    df = df.reset_index()
    df['id'] = df.index
    del df['minus_systole']
    del df['minus_next_shortest']
    start_index = {t:min(v) for t, v in df.groupby('tets').groups.items()}

    def new_name(row):
        t = row.tets
        i = row.id - start_index[t] + 1
        # See note at top about the below special case.
        if t == 8 and i in {300, 301}:
            i = ({300, 301} - {i}).pop()
        return 'K%d_%d' % (t, i)

    eight_301 = df.loc[500].copy()
    eight_300 = df.loc[501].copy()
    df.loc[500] = eight_300
    df.loc[501] = eight_301

    assert all(df['planned_name']==df.apply(new_name, axis=1))

    return df

def validate(dataframe):
    df = dataframe
    assert all((df.tets>=9)|(df.current_name==df.planned_name))

    A = np.asarray([df.tets, df.volume, df.systole, df.next_shortest]).transpose()
    deltas = np.abs(A[:-1] - A[1:])
    assert np.min(np.max(deltas, axis=1)) > 1e-5

    assert all(df.triangulation.apply(lambda x:x.split('_')[0]) == df.cusp_census_tri)
    assert all(df.hash==df.current_hash)
    dd = df[df.tets<9]
    #assert sum(dd.triangulation!=dd.current_tri) < 20
    assert all(dd.triangulation==dd.current_tri)


def compute_triangulation(task):
    M = snappy.Manifold(task['name'])
    meridian = a, b = eval(task['slope'])
    longitude = c, d = M.homological_longitude()
    if a*d - b*c < 0:
        longitude = (-c, -d)
    M.set_peripheral_curves([meridian, longitude])

    decs = fix_decorations.all_peripherals_encoded(M, task['cusp_census_tri'],
                            snappy.Triangulation, ignore_curve_orientations=True)
    task['triangulation'] = sorted(decs)[0]
    task['done'] = True

def add_hyp_data(task):
    M = snappy.ManifoldHP(task['name'])
    cs = float(M.chern_simons())
    if abs(cs) < 1e-20:
        cs = 0.0
    task['chernsimons'] = cs
    task['hash'] = snappy.db_utilities.db_hash(M)
    task['done'] = True

task = {'name':'m004', 'slope':'(1, 0)', 'cusp_census_tri':'cPcbbblxu'}

def save_data():
    df = load_and_sort()
    validate(df)
    df['id'] = df.index + 1
    df['name'] = df['planned_name']
    da = df[['id','name','cusps','betti','torsion','volume','chernsimons','tets','hash','triangulation']]
    da.to_csv('new_census_knots.csv', index=False)
    validate_saved()

def validate_saved():
    dnew = pd.read_csv('new_census_knots.csv', index_col=0)
    dnew = dnew[dnew.tets<9].copy()
    dold = pd.read_csv('../manifold_src/original_manifold_sources/census_knots.csv',
                       index_col=0)

    basic_cols = [col for col in dnew.columns if col not in ['chernsimons', 'volume']]
    for col in basic_cols:
        assert all(dnew[col] == dold[col])

    for col in ['volume', 'chernsimons']:
        assert (dnew[col] - dold[col]).abs().max() < 5e-11
    return dnew, dold

