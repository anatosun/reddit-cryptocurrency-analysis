import networkx as nx
import numpy as np
from networkx.utils import py_random_state

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

def louvain_partitions(graph):
    """This function implements the Louvain method.

    Args:
        graph (nx.Graph): a networkx graph.

    Returns:
        list: a list of sets corresponding to each community.
    """
    G = nx.Graph()
    G.add_nodes_from(graph)
    G.add_weighted_edges_from(graph.edges(data="weight", default=1))

    partitions = []

    while True:
        part = get_partition(G)
        partition, convergence = complete_partition(part, partitions)
    
        if convergence:
            break

        partitions.append(partition)
        G = create_graph(G, partition)
    
    return partitions

@py_random_state("seed")
def get_partition(G, hypernode=False, seed=None):
    """Return one passage of the Louvain method.

    Args:
        G (nx.Graph): a networkx graph.
        hypernode (boolean, optional): tell whether it is the first passage or not. Defaults to False.
        seed (int, optional): Indicator of random number generation state. Default None.

    Returns:
        list: a list of sets corresponding to each community.
    """
    partition = [{u} for u in G.nodes()]
    node_com = {u: i for i, u in enumerate(G.nodes())}
    rand_nodes = list(G.nodes)
    seed.shuffle(rand_nodes)
    loop = True
    nbrs = {u: {v for v in G[u] if v != u} for u in G}

    while loop:
        loop = False
        
        for node in rand_nodes:
            neighbors_com = set(node_com[j] for j in nbrs[node])
            best_com = max_dQ = -1
            
            for com in neighbors_com:
                dQ = gain(G, node, partition[com], hypernode=hypernode)

                if dQ > max_dQ:
                    max_dQ = dQ
                    best_com = com

            if max_dQ > 0 and best_com != node_com[node]:
                partition[node_com[node]].remove(node)
                partition[best_com].add(node)
                node_com[node] = best_com
                loop = True
                
    return [c for c in partition if c]

def gain(G, ni, nodes, hypernode=False):
    """Compute the modularity gain obtained by moving a node into a community.

    Args:
        G (nx.Graph): a networkx graph.
        ni (node index): node to move.
        nodes (set): set of nodes corresponding to a community.
        hypernode (boolean, optional): tell whether it is the first passage or not. Defaults to False.

    Returns:
        float: modularity gain obtained by moving a node into a community.
    """
    m = G.number_of_edges()
    
    dn = lambda n: G.degree[n]
    if hypernode:
        dn = lambda n: G[n][n]["weight"] if G.has_edge(n, n) else 0

    di = dn(ni)
    dj = sum(dn(nj) for nj in nodes if ni != nj)
    
    dij = 2 * sum(G[ni][nj]["weight"] for nj in nodes if G.has_edge(ni, nj) and ni != nj)

    return 0.5 * (dij - di * dj / m) / m

def complete_partition(part, partitions):
    """Reconstruct the complete Louvain partition based on the previous one.

    Args:
        part (list): one Louvain partitions.
        partitions (list): list of Louvain partitions.

    Returns:
        (part, boolean): a tuple containing the complete partition and a boolean telling whether the algorithm converge or not.
    """
    if not partitions:
        return part, False

    part_complete = []
    for com in part:
        tmp = set()
        for node in com:
            tmp |= partitions[-1][node] 
        part_complete.append(tmp)

    return part_complete, len(part) == len(partitions[-1])

def create_graph(G, partition):
    """Construct a new graph with the communities transformed into hypernodes.

    Args:
        G (nx.Graph): a networkx graph.
        partitions (list): a Louvain partitions.

    Returns:
        (nx.Graph): 
    """
    G2 = nx.Graph()
    node_com = {}
    
    for i, com in enumerate(partition):
        for node in com: 
            node_com[node] = i
        G2.add_node(i) 

    for node1, node2 in G.edges():
        com1, com2 = node_com[node1], node_com[node2]
        weight = 1 if com1 != com2 else 2
        if G2.has_edge(com1, com2):
            G2[com1][com2]["weight"] += weight
        else:
            G2.add_edge(com1, com2, weight=weight)

    return G2