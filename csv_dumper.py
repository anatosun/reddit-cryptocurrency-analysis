import json
import os
import pandas as pd

class CSVDumper():
    def __init__(self):
        self.edges = { 'deep_link' : {}, 'next_link': {}, 'cartesian_link' : [], 'deep_link_no_merge': [] }
        self.vertices = {}
        self.data = []
        
    def parse_json_file(self, file):
        with open(file, 'r') as f:
            subreddit = json.load(f)
            assert subreddit['subreddit'] is not None, "subreddit name cannot be None"
            assert subreddit['posts'] is not None, "subreddit posts cannot be empty"

            for post in subreddit['posts']:

                self.parse_comments_pd(post, subreddit['subreddit']) #for internal pd data frame

                self.parse_comments_deep_link(post['comments'], [(post['author'], 1)], subreddit['subreddit'])
                self.parse_comments_deep_link_no_merge(post['comments'], [(post['author'], 1)], subreddit['subreddit'])
                self.parse_comments_next_link(post['comments'], [(post['author'], 1)], subreddit['subreddit'])
                self.parse_comments_ucartesian_link(post['comments'], post['author'], subreddit['subreddit'])

    def parse_comments_pd(self, post, sub):
        self.data.append((post['id'], post['author'], post['score'], post['created_utc'], 1, sub))
        self.parse_comments_pd_r(post['comments'], sub)

    def parse_comments_pd_r(self, comments, sub):
        for comment in comments:
            self.data.append((comment['id'], comment['author'], comment['score'], comment['created_utc'], comment['depth'], sub))
            if len(comment['comments']) > 0:
                self.parse_comments_pd_r(comment['comments'], sub)

    def parse_comments_deep_link(self,comments,context, sub):
        for comment in comments:
            for prev_author, depth in context:
                if prev_author != comment['author']: #avoid self loops
                    key = (comment['author'], prev_author)
                    
                    #insert/update edge
                    if key not in self.edges['deep_link'].keys():
                        self.edges['deep_link'][key] = comment['score']/depth
                    else:
                        w = self.edges['deep_link'][key]
                        self.edges['deep_link'][key] = w + comment['score']/depth
                        
            if len(comment['comments']) > 0:
                self.parse_comments_deep_link(comment['comments'], context + [(comment['author'], comment['depth'])], sub)
    
    def parse_comments_next_link(self,comments,context, sub):
        for comment in comments:
            for prev_author, depth in context:
                if prev_author != comment['author']: #avoid self loops
                    key = (comment['author'], prev_author)
                    
                    #insert/update edge
                    if key not in self.edges['next_link'].keys():
                        self.edges['next_link'][key] = comment['score']/depth
                    else:
                        w = self.edges['next_link'][key]
                        self.edges['next_link'][key] = w + comment['score']/depth
                        
            if len(comment['comments']) > 0:
                self.parse_comments_next_link(comment['comments'], [context[0],(comment['author'], comment['depth'])], sub)
    
    def parse_comments_ucartesian_link_dump(self, folder):
        f = [ (tpl[0], tpl[1], 1) for tpls in self.edges['cartesian_link'] for tpl in tpls]
        p = pd.DataFrame(data=f, columns=["node1", "node2", "weight"])

        grouped = p.groupby(["node1", "node2"])
        s = grouped['weight'].agg('sum')
        s.to_csv(f"{folder}/edges_ucartesian.csv")

    def parse_comments_ucartesian_link(self,comments,post_author, sub):

        authors = [post_author]
        stack = []
        stack = comments
        while stack != []:
            comment = stack.pop()
            authors.append(comment['author'])

            if len(comment['comments']) > 0:
                stack = stack + comment['comments']

        #build unique cartesian product
        prd = []
        for x in authors:
            for y in authors:
                if x != y:
                    tpl = tuple(sorted((x,y)))
                    if tpl not in prd:
                        prd.append(tpl)

        self.edges['cartesian_link'].append(prd)




    def parse_comments_deep_link_no_merge(self,comments,context, sub):
        for comment in comments:
            for prev_author, depth in context:
                if prev_author != comment['author']: #avoid self loops
                    #"id","source", "target", "score", "weight", "time", "sub"
                    weight = comment['score']/depth
                    row = (comment['id'], comment['author'], prev_author, comment['score'], weight, comment['created_utc'], sub)
                    self.edges['deep_link_no_merge'].append(row)
                    
            if len(comment['comments']) > 0:
                self.parse_comments_deep_link_no_merge(comment['comments'], context + [(comment['author'], comment['depth'])], sub)
    
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
        
    def dump_edges(self, folder):
        l = ['next_link', 'deep_link']
        for link in l:
            file = f"{folder}/edges_{link}.csv"
            d = [ (source,target,weight) for (source,target), weight in self.edges[link].items() ]
            pd.DataFrame(columns = ["source", "target", "weight"],data=d).to_csv(file, index=False)

        #dump ucartesian
        self.parse_comments_ucartesian_link_dump(folder)

        #dump nomerge
        file = f"{folder}/edges_deep_link_no_merge.csv"
        pd.DataFrame(columns = ["id","source", "target", "score", "weight", "time", "sub"],data=self.edges['deep_link_no_merge']).to_csv(file, index=False)
    
    def dump_gephi(self,file):
        pass

    def debug(self):
        return self.data

if __name__ == "__main__":
    dp = CSVDumper()
    dp.parse_folder('test_data')
    dp.dump_scores('test_data/csv/scores.csv')
    dp.dump_active_subs('test_data/csv/subs.csv')
    dp.dump_edges('test_data/csv')
