import pandas as pd
import networkx as nx


class DegreeCentrality:
    
    def __init__(self):
        pass
    
    def compute_degree_centrality(self, G):
        self.n = G.number_of_nodes()
        self.G = G
        
        #load graph
        if isinstance(G, nx.DiGraph):
            self.load_digraph(G)
        else:
            self.load_graph(G)
            
        #compute degree stats
        self.df['deg_centr_max_poss_degree'] = self.df['degree']/(self.n-1)
        
        max_degree = self.df['degree'].max()
        self.df['deg_centr_max_degree'] = self.df['degree']/max_degree
        
        deg_sum = self.df['degree'].max()
        self.df['deg_centr_max_degree'] = self.df['degree']/max_degree
        
        self.df['deg_centr_degree_sum'] = self.df['degree']/G.number_of_edges()
        
        
        if self.digraph:
            self.df['deg_centr_max_degree_out'] = self.df['out_degree']/max_degree
            self.df['deg_centr_max_degree_in'] = self.df['in_degree']/max_degree
            
            self.df['deg_centr_max_poss_degree_out'] = self.df['out_degree']/(self.n-1)
            self.df['deg_centr_max_poss_degree_in'] = self.df['in_degree']/(self.n-1)

            self.df['deg_centr_degree_sum_out'] = self.df['out_degree']/G.number_of_edges()
            self.df['deg_centr_degree_sum_in'] = self.df['in_degree']/G.number_of_edges()
            
            
        return self.df
       
    
    def load_digraph(self, G):
        self.digraph = True
        degrees = [dict(G.degree()), dict(G.in_degree()), dict(G.out_degree())]
        data = {}
        for k in degrees[0].keys():
            data[k] = tuple(d[k] for d in degrees)
        
        self.df = pd.DataFrame.from_dict(data, columns=["degree", "in_degree", "out_degree"], orient='index')
        
            
    def load_graph(self, G):
        self.digraph = False
        self.df = pd.DataFrame.from_dict(dict(G.degree()), columns=["degree"], orient='index')
        
        
    def graph_degree_centrality(self):
        return nx.to_numpy_matrix(G).dot([1]*self.n)