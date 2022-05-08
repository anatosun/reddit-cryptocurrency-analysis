#copied this from some blog which turns out to have been copied from https://praw.readthedocs.io/en/v7.1.4/tutorials/refresh_token.html
from praw import Reddit
import random
import webbrowser
import sys
import socket
import os

def receive_connection():
    """
    Wait for and then return a connected socket..
    Opens a TCP connection on port 8080, and waits for a single client.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', 8080))
    server.listen(1)
    client = server.accept()[0]
    server.close()
    return client


def send_message(client, message):
    """
    Send message to client and close the connection.
    """
    client.send('HTTP/1.1 200 OK\r\n\r\n{}'.format(message).encode('utf-8'))
    client.close()


def main():
    user_agent = os.getenv('REDDIT_USER_AGENT')
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    client_username = os.getenv('REDDIT_CLIENT_USERNAME')
    client_password = os.getenv('REDDIT_CLIENT_PASSWORD')

    print(user_agent, client_id, client_secret, client_username, client_password)

    reddit = Reddit(user_agent=user_agent,
                    client_id=client_id,
                    client_secret=client_secret,
                    password=client_username,
                    username=client_password,
                    redirect_uri='http://localhost:8080')


    try:
        reddit.user.me()
        return 1
    except Exception as err:
        if (str(err) != 'invalid_grant error processing request'):
            print('LOGIN FAILURE')
        else:
            state = str(random.randint(0, 65000))
            scopes = ['identity', 'history', 'read', 'edit']
            url = reddit.auth.url(scopes, state, 'permanent')
            print('We will now open a window in your browser to complete the login process to reddit.')
            webbrowser.open(url)

            client = receive_connection()
            data = client.recv(1024).decode('utf-8')
            param_tokens = data.split(' ', 2)[1].split('?', 1)[1].split('&')
            params = {key: value for (key, value) in [token.split('=')
                                                    for token in param_tokens]}

            if state != params['state']:
                send_message(client, 'State mismatch. Expected: {} Received: {}'
                            .format(state, params['state']))
                return 0
            elif 'error' in params:
                send_message(client, params['error'])
                return 0

            refresh_token = reddit.auth.authorize(params["code"])
            send_message(client, "Refresh token: {}".format(refresh_token))

            print(refresh_token)
            return 1



if __name__ == "__main__":
    main()