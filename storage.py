from neo4j import GraphDatabase


class Neo4jConnection:

    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.driver is not None:
            self.driver.close()

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

    def insert_tweet(self, tweet):
        assert tweet['id'] is not None, "id cannot be None"
        assert tweet['datetime'] is not None, "datetime cannot be None"
        assert tweet['user_id'] is not None, "user_id cannot be None"
        assert tweet['username'] is not None, "username cannot be None"
        assert tweet['mentions'] is not None, "mentions cannot be None"
        assert tweet['tweet'] is not None, "tweet cannot be None"
        assert tweet['hashtags'] is not None, "hashtags cannot be None"
        user_id = tweet['user_id']
        username = tweet['username']
        tweet_id = tweet['id']
        tweet_content = str(tweet['tweet']).replace(
            '"', '\\"').replace("'", "\\'")
        time = tweet['datetime']
        hashtags = tweet['hashtags']
        qp = f'(p:Person {{id: {user_id}, username: "{username}"}})'
        self.query(f'MERGE {qp}')
        qt = f'(t:Tweet {{id: {tweet_id}, content: "{tweet_content}", datetime: "{time}"}})'
        self.query(f'MERGE {qt}')
        q = f'MATCH {qp}, {qt} MERGE (p)-[rel:POSTED]->(t)'
        self.query(q)
        for i in range(0, len(hashtags)):
            hashtag = str(hashtags[i]).lower()
            qh = f'(h:Hashtag {{id: "{hashtag}"}})'
            self.query(f'MERGE {qh}')
            q = f'MATCH {qt}, {qh} MERGE (t)-[:HAS]->(h)'
            self.query(q)
