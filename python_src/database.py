from __future__ import print_function
import sys, sqlite3, re, os, random

# This module uses sqlite3 databases with multiple tables.
# The path to the database file is specified at the module level.
from .sqlite_files import __path__ as manifolds_paths
manifolds_path = manifolds_paths[0]
database_path = os.path.join(manifolds_path, 'manifolds.sqlite')
alt_database_path = os.path.join(manifolds_path, 'more_manifolds.sqlite')
platonic_database_path = os.path.join(manifolds_path, 'platonic_manifolds.sqlite')

split_filling_info = re.compile('(.*?)((?:\([0-9 .+-]+,[0-9 .+-]+\))*$)')

def get_core_tables(ManifoldTable):
    """
    Functions such as this one are meant to be called in the
    __init__.py module in snappy proper.  To avoid circular imports,
    it takes as argument the class ManifoldTable from database.py in
    snappy. From there, it builds all of the Manifold tables from the
    sqlite databases manifolds.sqlite and more_manifolds.sqlite in
    manifolds_src, and returns them all as a list.
    """

    class ClosedManifoldTable(ManifoldTable):
        _select = 'select name, triangulation, m, l from %s '

        def __call__(self, **kwargs):
            return ClosedManifoldTable(self._table,
                                       db_path = database_path,
                                       **kwargs)

        def _finalize(self, M, row):
            """
            Give the closed manifold a name and do the Dehn filling.
            """
            M.set_name(row[0])
            M.dehn_fill(row[2:4])


    class OrientableCuspedCensus(ManifoldTable):
        """
        Iterator for all orientable cusped hyperbolic manifolds that
        can be triangulated with at most 9 ideal tetrahedra.

        >>> for M in OrientableCuspedCensus[3:6]: print(M, M.volume())
        ... 
        m007(0,0) 2.56897060
        m009(0,0) 2.66674478
        m010(0,0) 2.66674478
        >>> for M in OrientableCuspedCensus[-9:-6]: print(M, M.volume())
        ...
        o9_44241(0,0) 8.96323909
        o9_44242(0,0) 8.96736842
        o9_44243(0,0) 8.96736842
        >>> for M in OrientableCuspedCensus[4.10:4.11]: print(M, M.volume())
        ... 
        m217(0,0) 4.10795310
        m218(0,0) 4.10942659
        >>> for M in OrientableCuspedCensus(num_cusps=2)[:3]:
        ...   print(M, M.volume(), M.num_cusps())
        ... 
        m125(0,0)(0,0) 3.66386238 2
        m129(0,0)(0,0) 3.66386238 2
        m202(0,0)(0,0) 4.05976643 2
        >>> M = Manifold('m129')
        >>> M in LinkExteriors
        True
        >>> LinkExteriors.identify(M)
        5^2_1(0,0)(0,0)
        """

        _regex = re.compile('([msvt])([0-9]+)$|o9_\d\d\d\d\d$')

        def __init__(self, **kwargs):
           return ManifoldTable.__init__(self, table='orientable_cusped_view',
                                               db_path = database_path,
                                               **kwargs) 

    class NonorientableCuspedCensus(ManifoldTable):
        """
        Iterator for all orientable cusped hyperbolic manifolds that
        can be triangulated with at most 5 ideal tetrahedra.

        >>> for M in NonorientableCuspedCensus(betti=2)[:3]:
        ...   print(M, M.homology())
        ... 
        m124(0,0)(0,0)(0,0) Z/2 + Z + Z
        m128(0,0)(0,0) Z + Z
        m131(0,0) Z + Z
        """

        _regex = re.compile('[mxy]([0-9]+)$')
        
        def __init__(self, **kwargs):
           return ManifoldTable.__init__(self,
                                              table='nonorientable_cusped_view',
                                              db_path = database_path,
                                              **kwargs)

    class LinkExteriorsTable(ManifoldTable):
        """
        Link exteriors usually know a DT code describing the assocated link.
        """
        _select = 'select name, triangulation, DT from %s '

        def _finalize(self, M, row):
            M.set_name(row[0])
            M._set_DTcode(row[2])

    class LinkExteriors(LinkExteriorsTable):
        """
        Iterator for all knots with at most 11 crossings and links with
        at most 10 crossings, using the Rolfsen notation.  The triangulations
        were computed by Joe Christy.

        >>> for K in LinkExteriors(num_cusps=3)[-3:]:
        ...   print(K, K.volume())
        ... 
        10^3_72(0,0)(0,0)(0,0) 14.35768903
        10^3_73(0,0)(0,0)(0,0) 15.86374431
        10^3_74(0,0)(0,0)(0,0) 15.55091438
        >>> M = Manifold('8_4')
        >>> OrientableCuspedCensus.identify(M)
        s862(0,0)

        By default, the 'identify' returns the first isometric manifold it finds;
        if the optional 'extends_to_link' flag is set, it insists that meridians
        are taken to meridians.

        >>> M = Manifold('7^2_8')
        >>> LinkExteriors.identify(M)
        5^2_1(0,0)(0,0)
        >>> LinkExteriors.identify(M, extends_to_link=True)
        7^2_8(0,0)(0,0)
        """

        _regex = re.compile('([0-9]+_[0-9]+)$|[0-9]+[\^][0-9]+_[0-9]+$')
        
        def __init__(self, **kwargs):
           return ManifoldTable.__init__(self,
                                              table='link_exteriors_view',
                                              db_path = database_path,
                                              **kwargs)

        def __call__(self, *args, **kwargs):
            if args: # backwards compatibility for LinkExteriors
                if not isinstance(args[0], int) or len(args) > 1:
                    raise TypeError('Invalid specification for num_cusps.')
                if not 'num_cusps' in kwargs:
                    kwargs['num_cusps'] = args[0]
            return self.__class__(**kwargs)

        def _configure(self, **kwargs):
            """
            Process the ManifoldTable filter arguments and then add
            the ones which are specific to links.
            """
            ManifoldTable._configure(self, **kwargs)
            conditions = []

            flavor = kwargs.get('knots_vs_links', None)
            if flavor == 'knots':
                conditions.append('cusps=1')
            elif flavor == 'links':
                conditions.append('cusps>1')
            if 'crossings' in kwargs:
                N = int(kwargs['crossings'])
                conditions.append(
                    "(name like '%d^%%' or name like '%d|_%%' escape '|')"%(N,N))
            if self._filter:
                if len(conditions) > 0:
                    self._filter += (' and ' + ' and '.join(conditions))
            else:
                self._filter = ' and '.join(conditions)

    class HTLinkExteriors(LinkExteriorsTable):
        """
        Iterator for all knots and links up to 14 crossings as tabulated
        by Jim Hoste and Morwen Thistlethwaite.  In addition to the filter
        arguments supported by all ManifoldTables, this iterator provides
        alternating=<True/False>; knots_vs_links=<'knots'/'links'>; and
        crossings=N. These allow iterations only through alternating or
        non-alternating links with 1 or more than 1 component and a
        specified crossing number.

        >>> HTLinkExteriors.identify(LinkExteriors['8_20'])
        K8n1(0,0)
        >>> Mylist = HTLinkExteriors(alternating=False,knots_vs_links='links')[8.5:8.7]
        >>> len(Mylist)
        8
        >>> for L in Mylist:
        ...   print( L.name(), L.num_cusps(), L.volume() )
        ... 
        L11n138 2 8.66421454
        L12n1097 2 8.51918360
        L14n13364 2 8.69338342
        L14n13513 2 8.58439465
        L14n15042 2 8.66421454
        L14n24425 2 8.60676092
        L14n24777 2 8.53123093
        L14n26042 2 8.64333782
        >>> for L in Mylist:
        ...   print( L.name(), L.DT_code() )
        ... 
        L11n138 [(8, -10, -12), (6, -16, -18, -22, -20, -2, -4, -14)]
        L12n1097 [(10, 12, -14, -18), (22, 2, -20, 24, -6, -8, 4, 16)]
        L14n13364 [(8, -10, 12), (6, -18, 20, -22, -26, -24, 2, -4, -28, -16, -14)]
        L14n13513 [(8, -10, 12), (6, -20, 18, -26, -24, -4, 2, -28, -16, -14, -22)]
        L14n15042 [(8, -10, 14), (12, -16, 18, -22, 24, 2, 26, 28, 6, -4, 20)]
        L14n24425 [(10, -12, 14, -16), (-18, 26, -24, 22, -20, -28, -6, 4, -2, 8)]
        L14n24777 [(10, 12, -14, -18), (2, 28, -22, 24, -6, 26, -8, 4, 16, 20)]
        L14n26042 [(10, 12, 14, -20), (8, 2, 28, -22, -24, -26, -6, -16, -18, 4)]
        """

        _regex = re.compile('[KL][0-9]+[an]([0-9]+)$')
        
        def __init__(self, **kwargs):
           return LinkExteriorsTable.__init__(self,
                                         table='HT_links_view',
                                         db_path=alt_database_path,
                                         **kwargs)

        def _configure(self, **kwargs):
            """
            Process the ManifoldTable filter arguments and then add
            the ones which are specific to links.
            """
            ManifoldTable._configure(self, **kwargs)
            conditions = []

            alt = kwargs.get('alternating', None)
            if alt == True:
                conditions.append("name like '%a%'")
            elif alt == False:
                conditions.append("name like '%n%'")
            flavor = kwargs.get('knots_vs_links', None)
            if flavor == 'knots':
                conditions.append('cusps=1')
            elif flavor == 'links':
                conditions.append('cusps>1')
            if 'crossings' in kwargs:
                N = int(kwargs['crossings'])
                conditions.append(
                    "(name like '_%da%%' or name like '_%dn%%')"%(N,N))
            if self._filter:
                if len(conditions) > 0:
                    self._filter += (' and ' + ' and '.join(conditions))
            else:
                self._filter = ' and '.join(conditions)

    class CensusKnots(ManifoldTable):
        """
        Iterator for all of the knot exteriors in the SnapPea Census, as
        tabulated by Callahan, Dean, Weeks, Champanerkar, Kofman and
        Patterson.  These are the knot exteriors which can be triangulated
        by at most 7 ideal tetrahedra.

        >>> for M in CensusKnots[3.4:3.5]:
        ...   print(M, M.volume(), LinkExteriors.identify(M))
        ... 
        K4_3(0,0) 3.47424776 False
        K5_1(0,0) 3.41791484 False
        K5_2(0,0) 3.42720525 8_1(0,0)
        K5_3(0,0) 3.48666015 9_2(0,0)
        """
        
        _regex = re.compile('[kK][2-8]_([0-9]+)$')
        
        def __init__(self, **kwargs):
           return ManifoldTable.__init__(self,
                                              table='census_knots_view',
                                              db_path = database_path,
                                              **kwargs)

    class OrientableClosedCensus(ClosedManifoldTable):
        """
        Iterator for 11,031 closed hyperbolic manifolds from the census by
        Hodgson and Weeks.

        >>> len(OrientableClosedCensus)
        11031
        >>> len(OrientableClosedCensus(betti=2))
        1
        >>> for M in OrientableClosedCensus(betti=2):
        ...   print(M, M.homology())
        ... 
        v1539(5,1) Z + Z
        """
        def __init__(self, **kwargs):
           return ClosedManifoldTable.__init__(self,
                                                    table='orientable_closed_view',
                                                    db_path = database_path,
                                                    **kwargs) 

    class NonorientableClosedCensus(ClosedManifoldTable):
        """
        Iterator for 17 nonorientable closed hyperbolic manifolds from the
        census by Hodgson and Weeks.

        >>> for M in NonorientableClosedCensus[:3]: print(M, M.volume())
        ... 
        m018(1,0) 2.02988321
        m177(1,0) 2.56897060
        m153(1,0) 2.66674478
        """
        def __init__(self, **kwargs):
           return ClosedManifoldTable.__init__(self,
                                                    table='nonorientable_closed_view',
                                                    db_path = database_path,
                                                    **kwargs) 


    return [OrientableCuspedCensus(),
            NonorientableCuspedCensus(),
            OrientableClosedCensus(),
            NonorientableClosedCensus(),
            LinkExteriors(),
            CensusKnots(),
            HTLinkExteriors()]

def get_platonic_tables(ManifoldTable):
    
    class PlatonicManifoldTable(ManifoldTable):
        """
        Iterator for platonic hyperbolic manifolds.
        """

        def __init__(self, table = '', db_path = platonic_database_path,
                     **filter_args):

            ManifoldTable.__init__(self, table = table, db_path = db_path,
                                         **filter_args)

        def _configure(self, **kwargs):
            ManifoldTable._configure(self, **kwargs)
            conditions = []

            if 'solids' in kwargs:
                N = int(kwargs['solids'])
                conditions.append('solids = %d' % N)

            if self._filter:
                if len(conditions) > 0:
                    self._filter += (' and ' + ' and '.join(conditions))
            else:
                self._filter = ' and '.join(conditions)

    class TetrahedralOrientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the tetrahedral orientable cusped hyperbolic manifolds up to
        25 tetrahedra, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic tetrahedra.

        >>> for M in TetrahedralOrientableCuspedCensus(solids = 5):
        ...     print(M, M.volume())
        otet05_00000(0,0) 5.07470803
        otet05_00001(0,0)(0,0) 5.07470803
        >>> TetrahedralOrientableCuspedCensus.identify(Manifold("m004"))
        otet02_00001(0,0)


        """

        _regex = re.compile('otet\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                table = 'tetrahedral_orientable_cusped_census',
                **kwargs)

    class TetrahedralNonorientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the tetrahedral non-orientable cusped hyperbolic manifolds up to
        21 tetrahedra, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic tetrahedra.

        >>> len(TetrahedralNonorientableCuspedCensus)
        25194
        >>> list(TetrahedralNonorientableCuspedCensus[:1.3])
        [ntet01_00000(0,0)]

        """

        _regex = re.compile('ntet\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'tetrahedral_nonorientable_cusped_census',
                **kwargs)

    class OctahedralOrientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the octahedral orientable cusped hyperbolic manifolds up to
        7 octahedra, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic octahedra.

            >>> OctahedralOrientableCuspedCensus.identify(Manifold("5^2_1"))
            ooct01_00001(0,0)(0,0)

        For octahedral manifolds that are also the complement of an `Augmented
        Knotted Trivalent Graph (AugKTG) <http://arxiv.org/abs/0805.0094>`_, the
        corresponding link is included::

            >>> M = OctahedralOrientableCuspedCensus['ooct04_00034']
            >>> M.link()
            <Link: 4 comp; 17 cross>

        The link can be viewed with ``M.plink()``. To only see complements of
        AugKTGs, supply ``isAugKTG = True``::

         >>> len(OctahedralOrientableCuspedCensus(isAugKTG = True))
         238
         >>> for M in OctahedralOrientableCuspedCensus(isAugKTG = True)[:5]:
         ...     print(M, M.link().DT_code(DT_alpha=True))
         ooct02_00001(0,0)(0,0)(0,0)(0,0) DT[mdbceceJamHBlCKgdfI]
         ooct02_00002(0,0)(0,0)(0,0) DT[lcgbcIkhLBJecGaFD]
         ooct02_00003(0,0)(0,0)(0,0) DT[icebbGIAfhcEdB]
         ooct02_00005(0,0)(0,0)(0,0) DT[hcdbbFHegbDAc]
         ooct04_00027(0,0)(0,0)(0,0)(0,0) DT[zdpecbBujVtiWzsLQpxYREadhOKCmFgN]


        """

        _select = 'select name, triangulation, DT from %s '
        _regex = re.compile('ooct\d+_\d+')

        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'octahedral_orientable_cusped_census',
                **kwargs)

        def _configure(self, **kwargs):
            PlatonicManifoldTable._configure(self, **kwargs)
            conditions = []

            if 'isAugKTG' in kwargs:
                if kwargs['isAugKTG']:
                    conditions.append('isAugKTG = 1')
                else:
                    conditions.append('isAugKTG = 0')

            if self._filter:
                if len(conditions) > 0:
                    self._filter += (' and ' + ' and '.join(conditions))
            else:
                self._filter = ' and '.join(conditions)

        def _finalize(self, M, row):
            PlatonicManifoldTable._finalize(self, M, row)
            if row[2] and not row[2]=='Null':
                M._set_DTcode(row[2])

    class OctahedralNonorientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the octahedral non-orientable cusped hyperbolic manifolds up to
        5 octahedra, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic octahedra.

        >>> for M in OctahedralNonorientableCuspedCensus(solids = 3, betti = 3,cusps = 4):
        ...     print(M, M.homology())
        noct03_00007(0,0)(0,0)(0,0)(0,0) Z/2 + Z + Z + Z
        noct03_00029(0,0)(0,0)(0,0)(0,0) Z/2 + Z + Z + Z
        noct03_00047(0,0)(0,0)(0,0)(0,0) Z/2 + Z + Z + Z
        noct03_00048(0,0)(0,0)(0,0)(0,0) Z/2 + Z + Z + Z

        """

        _regex = re.compile('noct\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'octahedral_nonorientable_cusped_census',
                **kwargs)

    class CubicalOrientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the cubical orientable cusped hyperbolic manifolds up to
        7 cubes, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic octahedra.

        >>> M = TetrahedralOrientableCuspedCensus['otet05_00001']
        >>> CubicalOrientableCuspedCensus.identify(M)
        ocube01_00002(0,0)(0,0)

        """

        _regex = re.compile('ocube\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'cubical_orientable_cusped_census',
                **kwargs)

    class CubicalNonorientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the cubical non-orientable cusped hyperbolic manifolds up to
        5 cubes, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic octahedra.

        >>> for M in CubicalNonorientableCuspedCensus[-3:]:
        ...     print(M, M.volume())
        ncube05_30945(0,0) 25.37354016
        ncube05_30946(0,0)(0,0) 25.37354016
        ncube05_30947(0,0)(0,0) 25.37354016

        """

        _regex = re.compile('ncube\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'cubical_nonorientable_cusped_census',
                **kwargs)

    class DodecahedralOrientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the dodecahedral orientable cusped hyperbolic manifolds up to
        2 dodecahedra, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic dodecahedra.

        Complement of one of the dodecahedral knots by Aitchison and Rubinstein::

          >>> M=DodecahedralOrientableCuspedCensus['odode02_00913']
          >>> M.dehn_fill((1,0))
          >>> M.fundamental_group()
          Generators:
          <BLANKLINE>
          Relators:
          <BLANKLINE>

        """

        _regex = re.compile('odode\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'dodecahedral_orientable_cusped_census',
                **kwargs)

    class DodecahedralNonorientableCuspedCensus(PlatonicManifoldTable):
        """
        Iterator for the dodecahedral non-orientable cusped hyperbolic manifolds up to
        2 dodecahedra, i.e., manifolds that admit a tessellation by regular ideal
        hyperbolic dodecahedra.

        >>> len(DodecahedralNonorientableCuspedCensus)
        4146

        """
        
        _regex = re.compile('ndode\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'dodecahedral_nonorientable_cusped_census',
                **kwargs)

    class IcosahedralNonorientableClosedCensus(PlatonicManifoldTable):
        """
        Iterator for the icosahedral non-orientable closed hyperbolic manifolds up
        to 3 icosahedra, i.e., manifolds that admit a tessellation by regular finite
        hyperbolic icosahedra.

        >>> list(IcosahedralNonorientableClosedCensus)
        [nicocld02_00000(1,0)]

        """
        
        _regex = re.compile('nicocld\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'icosahedral_nonorientable_closed_census',
                **kwargs)

    class IcosahedralOrientableClosedCensus(PlatonicManifoldTable):
        """
        Iterator for the icosahedral orientable closed hyperbolic manifolds up
        to 4 icosahedra, i.e., manifolds that admit a tessellation by regula finite
        hyperbolic icosahedra.

        >>> M = IcosahedralOrientableClosedCensus[0]
        >>> M.volume()
        4.68603427
        >>> M
        oicocld01_00000(1,0)
        """

        _regex = re.compile('oicocld\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'icosahedral_orientable_closed_census',
                **kwargs)

    class CubicalNonorientableClosedCensus(PlatonicManifoldTable):
        """
        Iterator for the cubical non-orientable closed hyperbolic manifolds up
        to 10 cubes, i.e., manifolds that admit a tessellation by regular finite
        hyperbolic cubes.

        >>> len(CubicalNonorientableClosedCensus)
        93

        """

        _regex = re.compile('ncube\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'cubical_nonorientable_closed_census',
                **kwargs)

    class CubicalOrientableClosedCensus(PlatonicManifoldTable):
        """
        Iterator for the cubical orientable closed hyperbolic manifolds up
        to 10 cubes, i.e., manifolds that admit a tessellation by regular finite
        hyperbolic cubes.

        >>> len(CubicalOrientableClosedCensus)
        69

        """

        _regex = re.compile('ocube\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'cubical_orientable_closed_census',
                **kwargs)

    class DodecahedralNonorientableClosedCensus(PlatonicManifoldTable):
        """
        Iterator for the dodecahedral non-orientable closed hyperbolic manifolds up
        to 2 dodecahedra, i.e., manifolds that admit a tessellation by regular finite
        hyperbolic dodecahedra with a dihedral angle of 72 degrees.

        >>> DodecahedralNonorientableClosedCensus[0].volume()
        22.39812948

        """

        _regex = re.compile('ndodecld\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'dodecahedral_nonorientable_closed_census',
                **kwargs)

    class DodecahedralOrientableClosedCensus(PlatonicManifoldTable):
        """
        Iterator for the dodecahedral orientable closed hyperbolic manifolds up
        to 3 dodecahedra, i.e., manifolds that admit a tessellation by regular finite
        hyperbolic dodecahedra with a dihedral angle of 72 degrees.

        The Seifert-Weber space::

          >>> M = DodecahedralOrientableClosedCensus(solids = 1)[-1]
          >>> M.homology()
          Z/5 + Z/5 + Z/5

        """

        _regex = re.compile('ododecld\d+_\d+')
        
        def __init__(self, **kwargs):
            return PlatonicManifoldTable.__init__(
                self,
                'dodecahedral_orientable_closed_census',
                **kwargs)

    return [TetrahedralOrientableCuspedCensus(),
            TetrahedralNonorientableCuspedCensus(),
            OctahedralOrientableCuspedCensus(),
            OctahedralNonorientableCuspedCensus(),
            CubicalOrientableCuspedCensus(),
            CubicalNonorientableCuspedCensus(),
            DodecahedralOrientableCuspedCensus(),
            DodecahedralNonorientableCuspedCensus(),
            IcosahedralNonorientableClosedCensus(),
            IcosahedralOrientableClosedCensus(),
            CubicalNonorientableClosedCensus(),
            CubicalOrientableClosedCensus(),
            DodecahedralNonorientableClosedCensus(),
            DodecahedralOrientableClosedCensus()]

def get_tables(ManifoldTable):
    """
    This function is meant to be called in the __init__.py module in
    snappy proper. To avoid circular imports, it takes as argument the
    class ManifoldTable from database.py in snappy. From there, it
    builds all of the Manifold tables from the sqlite databases
    manifolds.sqlite and more_manifolds.sqlite in manifolds_src, and
    returns them all as a list.
    """
    return get_core_tables(ManifoldTable) + get_platonic_tables(ManifoldTable)



def connect_to_db(db_path):
    """
    Open the given sqlite database, ideally in read-only mode.
    """
    if sys.version_info >= (3,4):
        uri = 'file:' + db_path + '?mode=ro'
        return sqlite3.connect(uri, uri=True)
    elif sys.platform.startswith('win'):
        try:
            import apsw
            return apsw.Connection(db_path, flags=apsw.SQLITE_OPEN_READONLY)
        except ImportError:
            return sqlite3.connect(db_path)
    else:
        return sqlite3.connect(db_path)

def get_DT_tables():
    """
    Returns two barebones databases for looking up DT codes by name. 
    """
    class DTCodeTable(object):
        """
        A barebones database for looking up a DT code by knot/link name.
        """
        def __init__(self, name='', table='',db_path=database_path, **filter_args):
            self._table = table
            self._select = 'select DT from {}'.format(table)
            self.name = name
            
            self._connection = connect_to_db(db_path)
            self._cursor = self._connection.cursor()

        def __repr__(self):
            return self.name

        def __getitem__(self, link_name):
            select_query = self._select + ' where name="{}"'.format(link_name)
            return self._cursor.execute(select_query).fetchall()[0][0]

        def __len__(self):
            length_query = 'select count(*) from ' + self._table
            return self._cursor.execute(length_query).fetchone()[0]

    RolfsenDTcodes = DTCodeTable(name = 'RolfsenDTcodes',
                                   table = 'link_exteriors',
                                   db_path = database_path)
    HTLinkDTcodes = DTCodeTable(name = 'HTLinkDTcodes',
                                  table = 'HT_links',
                                  db_path = alt_database_path)
    return [RolfsenDTcodes, HTLinkDTcodes]
