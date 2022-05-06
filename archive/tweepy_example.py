import os
import tweepy
import numpy as np


class Scraper:
    def __init__(self, api_bearer):
        self.client = tweepy.Client(api_bearer)
        # self.follower_limit = 180

    def get_followers(self, username=None, id=None):
        assert username is not None or id is not None, 'username and id cannot both be None'
        start_node_id = id if id is not None else self.client.get_user(
            username=username).data['id']
        running = True
        next_token = None
        followers = np.array([])
        while running:
            start_node_friends = self.client.get_users_followers(
                id=start_node_id, max_results=1000, pagination_token=next_token)
            if len(start_node_friends.errors) != 0:
                print(start_node_friends.errors)
                running = False

            np.append(followers, start_node_friends.data)
            if start_node_friends.meta.get('next_token') is not None:
                next_token = start_node_friends.meta.get('next_token')
            else:
                running = False
        return followers


if __name__ == "__main__":
    BEARER = os.getenv('API_BEARER')
    scraper = Scraper(BEARER)
    followers = scraper.get_followers(username='SuisseSUI')
