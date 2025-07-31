import snappy


def isosig(manifold):
    return manifold.triangulation_isosig(ignore_cusp_ordering=True,
                                         ignore_curve_orientations=True,
                                         ignore_orientation=True)


def isomorphic_triangulations_preserving_links(A, B):
    isomorphisms = A.isomorphisms_to(B)
    return any(isom.extends_to_link for isom in isomorphisms)


def same_link_exterior_no_geometry(A, B, max_tries=10000):
    """
    Without using any hyperbolic geometry, use randomization to try to
    stumble across identical triangulations of the exteriors of the
    given links.

    >>> A = snappy.Link('L14n62566')
    >>> B = snappy.Link('L14n63195')
    >>> same_link_exterior_no_geometry(A, B)
    True

    If ``True`` is returned, the links are definitely the same, but
    ``False`` only means it failed to find an isomorphism.
    """

    T = A.exterior(with_hyperbolic_structure=False)
    S = B.exterior(with_hyperbolic_structure=False)
    target = isosig(T)
    for i in range(max_tries):
        if isosig(S) == target:
            break
        S.randomize()

    return isomorphic_triangulations_preserving_links(T, S)


def find_duplicates_using_hyperbolic_geometry(filename='/tmp/dups'):
    outfile = open(filename, 'w')
    for M in snappy.HTLinkExteriors(knots_vs_links='links'):
        if M.solution_type(enum=2) in {1, 2}:
            N = snappy.HTLinkExteriors.identify(M, extends_to_link=True)
            if N.name() != M.name():
                outfile.write(N.name() + ',' + M.name() + '\n')
                outfile.flush()



if __name__ == '__main__':
    import doctest
    doctest.testmod()
