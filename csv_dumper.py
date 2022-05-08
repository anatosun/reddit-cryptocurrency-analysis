import json
import os
import pandas as pd

class CSVDumper():
    def __init__(self):
        self.edges = {} # keys=(source,target), val weight
        self.vertices = {}
        self.data = []
        
    def parse_json_file(self, file):
        with open(file, 'r') as f:
            subreddit = json.load(f)
            assert subreddit['subreddit'] is not None, "subreddit name cannot be None"
            assert subreddit['posts'] is not None, "subreddit posts cannot be empty"
            
            for post in subreddit['posts']:
                self.parse_comments(post['comments'], [(post['author'], 1)], subreddit['subreddit'])
            
                
    def parse_comments(self,comments,context, sub):
        for comment in comments:
            current_comment_author = comment['author']
            for prev_author, depth in context:
                if prev_author != current_comment_author: #avoid self loops
                    key = (current_comment_author, prev_author)
                    
                    #insert/update edge
                    if key not in self.edges.keys():
                        self.edges[key] = comment['score']/depth
                    else:
                        w = self.edges[key]
                        self.edges[key] = w + comment['score']/depth
                        
                    #add to data
                    self.data.append((comment['id'], comment['author'], comment['score'], comment['created_utc'], comment['depth'], sub))
                    
            if len(comment['comments']) > 0:
                self.parse_comments(comment['comments'], context + [(current_comment_author, comment['score'])], sub)
    
    def parse_folder(self, folder):
        for file in os.listdir(os.path.join(folder)):
            if file.endswith(".json"):
                self.parse_json_file(os.path.join(folder, file))

    def prep_df(self):
        df = pd.DataFrame(columns = ["id", "author", "score", "created_utc", "depth","subreddit"], data=self.data)
        df = df.astype({'created_utc': 'int64'})
        df['created_utc'] = pd.to_datetime(df['created_utc'], unit='s')
        return df
    
    def dump_scores(self,file):
        grouped_df = self.prep_df().groupby(["author"])
        s = grouped_df['score'].agg('sum')
        s.index.names = ['Id']
        s.to_csv(file)

    def dump_active_subs(self,file):
        df = self.prep_df()
        g = df[["author", "subreddit"]].groupby(["author"])
        g = g['subreddit'].apply(list)
        g.index.names = ['Id']
        g.to_csv(file)
        
    def dump_edges(self, file):
        d = [ (source,target,weight) for (source,target), weight in self.edges.items() ]
        pd.DataFrame(columns = ["source", "target", "weight"],data=d).to_csv(file, index=False)
    
    def dump_gephi(self,file):
        pass

if __name__ == "__main__":
    dp = EdgeListDumper()
    dp.parse_folder('../data')
    dp.dump_scores('../data/csv/scores.csv')
    dp.dump_active_subs('../data/csv/subs.csv')
    dp.dump_edges('../data/csv/edges.csv')
