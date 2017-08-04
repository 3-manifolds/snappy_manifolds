def is_group_unchanged_by_to_from_string(A):
    def group_info(M):
        G = M.fundamental_group(False, False, False, False)
        return (G.relators(), G.peripheral_curves())
    B = snappy.Manifold(A._to_string())
    return group_info(A) == group_info(B)

def data_of_triangulation(M):
    tets = M._get_tetrahedra_gluing_data()
    curves = M._get_peripheral_curve_data()

    # The rest of the tests should be redundant but better safe
    # than sorry; indeed, initially I found an annoying glitch in
    # SnapPy this way, which was fixed in the latest commit.
    # Still, might want to surpress when generating the initial
    # files for speed reasons.

    eqns = M.gluing_equations().list()
    G = M.fundamental_group()
    group = [G.generators(), G.relators(), G.peripheral_curves()]

    H = M.fundamental_group(False, False, False, False)
    group_alt = [H.generators(), H.relators(), H.peripheral_curves()]
    return (tets, curves, eqns, group, group_alt)

def same_labeled_triangulation_and_peripheral_curves(A, B, weakly=False):
    """
    Returns true only if the triangulations are the same as *labeled*
    complexes and the peripheral curves are *identical* normal curves.
    """
    if weakly:
        return data_of_triangulation(A)[:2] == data_of_triangulation(B)[:2]
    else:
        return data_of_triangulation(A) == data_of_triangulation(B)
