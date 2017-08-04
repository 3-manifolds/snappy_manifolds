The SnapPy manifold database
============================

This repository stores the core manifold databases that come with
SnapPy, and includes the source code for the Python module
"snappy_manifolds" which packages them up for use in SnapPy and
Spherogram.

The raw source for the tables are in::
  
  manifold_src/original_manifold_sources

stored as plain text CSV files for the potential convenience of other
users. The triangulations themselves are stored in the "isosig" format
of Burton, as described in the appendix to `this paper
<http://arxiv.org/abs/1110.6080>`_ with an added "decoration" suffix
that describes the peripheral framing.
