import networkx as nx
import numpy as np


def page_rank(G: nx.digraph,
              iterations=100,
              alpha=0.85,
              error=1.0e-6) -> dict:
    """This function implements the PageRank algorithm.

    Args:
        G (nx.digraph): a networkx digraph
        iterations (int, optional): number of maximum iterations. Defaults to 100.
        alpha (float, optional): damping factor. Defaults to 0.85.
        error (float, optional): error threshold to reach to break the iterations. Defaults to 1.0e-6.

    Returns:
        dict: a dictionary of nodes and their PageRank values
    """
    if len(G) == 0:
        return {}

    nodes = list(G)

    A = nx.to_numpy_array(G,
                          nodelist=nodes,
                          weight="weight",
                          dtype=float)
    n, m = A.shape

    if n == 0:
        return {}

    S = A.sum(axis=1)
    S[S != 0] = 1.0 / S[S != 0]

    Q = np.zeros((n, m))
    np.fill_diagonal(Q, S.T.flatten())
    A = Q.dot(A)
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
