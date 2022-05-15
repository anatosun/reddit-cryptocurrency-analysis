import networkx as nx
import numpy as np
import scipy as sp


def page_rank(G: nx.digraph, iterations=100, alpha=0.85, error=1.0e-6):

    if len(G) == 0:
        return {}

    nodes = list(G)

    A = nx.to_numpy_array(G, nodelist=nodes, weight="weight", dtype=float)
    n, _ = A.shape

    if n == 0:
        return {}

    S = A.sum(axis=1)
    S[S != 0] = 1.0 / S[S != 0]

    A = sp.sparse.csr_array(sp.sparse.spdiags(S.T, 0, *A.shape)).dot(A)

    x = np.ones(n)/n
    p = np.ones(n)/n

    for _ in range(iterations):
        y = x
        x = alpha * \
            (x.dot(A) +
             sum(x[np.where(S == 0)[0]]) * p) + \
            (1 - alpha) * p
        err = np.absolute(x - y).sum()
        if err < n * error:
            return dict(zip(nodes, map(float, x)))
    return dict(zip(nodes, map(float, x)))
