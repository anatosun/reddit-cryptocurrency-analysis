import os
import tweepy


if __name__ == "__main__":
    client = tweepy.Client(os.getenv('API_BEARER'))
    start_node_id = client.get_user(username='elonmusk').data['id']
    running = True
    next_token = None
    while running:
        start_node_friends = client.get_users_followers(
            id=start_node_id, max_results=10, pagination_token=next_token)
        if len(start_node_friends.errors) != 0:
            print(start_node_friends.errors)
            running = False
        elon_friends_ids = [f['id'] for f in start_node_friends.data]
        print(start_node_friends)
        next_token = start_node_friends.meta['next_token']
