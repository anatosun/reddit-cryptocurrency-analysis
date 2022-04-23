#######
# IMPORT PACKAGES
#######

import praw
from praw.models import SubredditHelper, Submission, Comment, MoreComments, ListingGenerator, Redditor
from praw.models.comment_forest import CommentForest
import json
import os


def main():
    user_agent = os.getenv('REDDIT_USER_AGENT')
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    reddit = praw.Reddit(user_agent=user_agent,
                         client_id=client_id,
                         client_secret=client_secret)
    subreddits = ["Cryptocurrency", "Bitcoin", "Ethereum", "Askreddit"]
    queries = ["Bitcoin", "Ethereum", "Cryptocurrency"]
    s: str
    for s in subreddits:
        subreddit: SubredditHelper = reddit.subreddit(s)
        file = f"{subreddit.display_name}.json"
        schema = {
            "subreddit": subreddit.display_name,
            "queries": queries,
            "type": subreddit.subreddit_type,
            "posts": []
        }
        for q in queries:

            listing: ListingGenerator = subreddit.search(
                q, sort="hot", limit=1)
            for submission in listing:
                ss = submission_schema(submission=submission)
                schema['posts'].append(ss)
                with open(file, 'w') as f:
                    print(file)
                    json.dump(schema, f, indent=4)
            # for post in reddit.subreddit(subreddit).new(limit=1000):
            #     dump_replies(replies=post.comments, context=[post.title])


def submission_schema(submission: Submission):
    subreddit: str = submission.subreddit.display_name
    schema = {}
    schema['title'] = submission.title
    schema['url'] = submission.url
    schema['author'] = submission.author.name
    schema['created_utc'] = submission.created_utc
    schema['id'] = submission.id
    schema['score'] = submission.score
    schema['num_comments'] = submission.num_comments
    schema['subreddit'] = subreddit

    schema['comments'] = fetch_comments_schema(
        comments=submission.comments, context=[submission.title])

    return schema


def fetch_comments_schema(comments: CommentForest, context):
    fetched = []
    comment: Comment
    for comment in comments:
        if isinstance(comment, praw.models.MoreComments):
            continue

        data = {
            "author": fetch_author_schema(author=comment.author),
            "score": comment.score,
            "response": comment.body,
            "comments": []
        }

        context.append(comment.body)
        data["comments"] = fetch_comments_schema(comment.replies, context)
        context.pop()
        fetched.append(data)
    return fetched


def fetch_author_schema(author: Redditor):
    return {
        "author": author.name,
        "created_utc": author.created_utc,
        "id": author.id,
        "link_karma": author.link_karma,
        "comment_karma": author.comment_karma,
        "is_employee": author.is_employee,
        "has_verified_email": author.has_verified_email
    }


if __name__ == "__main__":
    main()
