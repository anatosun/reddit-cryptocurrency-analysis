import networkx as nx
import numpy as np
import timeit
import resource


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


def test_page_rank():
    import pandas as pd
    G = nx.from_pandas_edgelist(pd.read_csv(
        './data/edgelist.csv'), create_using=nx.DiGraph())
    start = timeit.default_timer()
    nx_ranks = nx.pagerank(G)
    stop = timeit.default_timer()
    nx_time = stop - start
    print('networkx pagerank computation time: {}s'.format(nx_time))
    nx_memory = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
    print('networkx pagerank memory usage: {}MB'.format(nx_memory))
    start = timeit.default_timer()
    own_ranks = page_rank(G)
    stop = timeit.default_timer()
    own_time = stop - start
    own_memory = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
    print('own pagerank implementation computation time: {}s'.format(own_time))
    print('own pagerank implementation memory usage: {}MB'.format(own_memory))
    overall_error = np.array(
        [np.absolute(own_ranks[k]-nx_ranks[k]) for k in own_ranks.keys()]).sum()
    print(
        f"overall_error from own implementation to networkx's one: {overall_error}")


def main():
    test_page_rank()


if __name__ == "__main__":
    main()
