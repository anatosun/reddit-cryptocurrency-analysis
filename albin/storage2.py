from neo4j import GraphDatabase

import json
import os


class Neo4jConnection:

    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.driver is not None:
            try:
                self.driver.close()
            except Exception as e:
                print("Failed to close driver:", e)

    def query(self, query, parameters=None, db=None):
        assert self.driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = self.driver.session(
                database=db) if db is not None else self.driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response

    def insert_post(self, post: dict, sub):
        assert post['title'] is not None, "title cannot be None"
        assert post['url'] is not None, "url cannot be None"
        assert post['author'] is not None, "author cannot be None"
        assert post['created_utc'] is not None, "created_utc cannot be None"
        assert post['id'] is not None, "id cannot be None"
        assert post['score'] is not None, "score cannot be None"
        assert post['num_comments'] is not None, "num_comments cannot be None"
        assert post['subreddit'] is not None, "subreddit cannot be None"
        self.insert_comments(post['comments'], [(post['author'], 1)])

    def insert_comments(self, comments: list, context: list):
        for comment in comments:
            assert comment['author'] is not None, "author cannot be None"
            assert comment['score'] is not None, "score cannot be None"
            assert comment['created_utc'] is not None, "created_utc cannot be None"
            assert comment['response'] is not None, "response cannot be None"
            assert comment['depth'] is not None, "depth cannot be None"
            # author query ###### username: author
            query_author = f"MERGE (n:User {{username: '{comment['author']}'}})"
            self.query(query_author)
            for a, d in context:
                if a != comment['author']:
                    # context query ###### username: author
                    query_context_author = f"MERGE (n:User {{username: '{a}'}})"
                    self.query(query_context_author)
                    # relation query ###### weight: score/depth
                    query_relation = f"""MATCH
                    (a:User {{username: '{comment['author']}'}}),
                    (b:User {{username: '{a}'}})
                    MERGE (a)-[r:COMMENTED {{weight: {comment['score']/d}}}]->(b)
                    ON CREATE 
                        SET r.weight = {comment['score']/d}
                    ON MATCH 
                        SET r.weight = r.weight + {comment['score']/d}
                    """
                    self.query(query_relation)

            if len(comment['comments']) > 0:
                self.insert_comments(
                    comment['comments'], context + [(comment['author'], comment['score'])])

    def insert_json_dump(self, file: str):

        with open(file, 'r') as f:
            subreddit = json.load(f)
            assert subreddit['subreddit'] is not None, "subreddit name cannot be None"
            assert subreddit['posts'] is not None, "subreddit name cannot be None"
            for post in subreddit['posts']:
                self.insert_post(post, subreddit['subreddit'])


if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "neo"
    db = "reddit"
    nc = Neo4jConnection(uri, user, password)
    for file in os.listdir(os.path.join('data')):
        if file.endswith(".json"):
            nc.insert_json_dump(os.path.join('data', file))
