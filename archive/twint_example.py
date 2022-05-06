import twint
import sys
import json
import storage

module = sys.modules["twint.storage.write"]
db = storage.Neo4jConnection(
    uri="bolt://localhost:7687", user="neo4j", password="neo")


def Json(obj, config):
    tweet = obj.__dict__
    db.insert_tweet(tweet)


module.Json = Json
c = twint.Config()
c.Popular_tweets = True
c.Search = "bitcoin OR btc OR ethereum OR ether OR eth OR riple OR cryptocurrency OR monero OR blockchain OR coin OR currency OR ico OR ltc OR mining"
c.Show_hashtags = False
c.Min_likes = 10
c.Store_json = True
c.Custom["user"] = ["id", "tweet", "user_id",
                    "username", "hashtags", "mentions"]
c.Output = "tweets.json"
c.Since = "2019-05-20"
c.Lang = "en"
c.Hide_output = True

twint.run.Search(c)
