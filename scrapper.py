from praw import Reddit
from praw.models import SubredditHelper, Submission, Comment, MoreComments, ListingGenerator, Redditor
from praw.models.comment_forest import CommentForest
from concurrent.futures import ProcessPoolExecutor as Pool
from multiprocessing import cpu_count, Lock
import json
import os
import datetime
import reddit2fa_connector
import sys
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


#config
data_path = os.path.join("data")
logs_path = os.path.join("data/logs")
min_score = 3
limit = 1000
sorting_options = ["hot", "top", "new"]
subreddits = ["Bitcoin", "Ethereum", "Dogecoin", "BitcoinBeginners", "CryptoCurrencies", "CryptoTechnology", "CryptoMarkets", "Binance", "CoinBase", "btc"]

def logger(string, file, overwrite=False):
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)
    file_path = os.path.join(logs_path, f"{file}.log")
    with open(file_path, 'w' if overwrite else 'a') as f:
        ts = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        line = f"[{ts}] {string}\n"
        #print(f"[{ts}] {string}")
        f.write(line)


def main():

    # login to get refresh token
    #reddit2fa_connector.connect()

    # Prepare Pools & PRAW
    pool = Pool(max_workers=cpu_count())
    user_agent = os.getenv('REDDIT_USER_AGENT')
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    refresh_token = os.getenv('REDDIT_REFRESH_TOKEN')

    reddit = Reddit(user_agent=user_agent,
                    client_id=client_id,
                    client_secret=client_secret,
                    refresh_token=refresh_token)
    
    # Create folders
    if not os.path.exists(data_path):
        os.mkdir(data_path)
        os.mkdir(data_path+"/ids")

    #crawl
    ps = []
    for s in subreddits:
        subreddit = reddit.subreddit(s)
        ids_file = os.path.join(data_path, f"ids/{subreddit.display_name}.txt")

        existing_posts = parse_existing_ids(ids_file)

        ps.append((pool.submit(
            save_subreddit,
            subreddit,
            existing_posts,
            data_path,
            sorting_options,
            limit,
            min_score)),)

    for s, p in enumerate(ps):
        logger(f"finished job for {subreddits[s]}; errors: {p.exception()}", "main")
        print(p.result())


def parse_existing_ids(file):
    if os.path.exists(file):
        df = pd.read_csv(file, header=0, index_col=0)
    else:
        df = pd.DataFrame(columns = ['id','ts', 'num_comments'])
        df.set_index('id', inplace=True)
    
    return df

def store_ids(file, existing_posts, ts, new_posts, new_posts_num_comments):
    #prepare ids file
    crawl_tss = [ts]*len(new_posts)
    df_new_posts = pd.DataFrame(columns = ['id','ts', 'num_comments'], data=list(zip(new_posts, crawl_tss,new_posts_num_comments)))
    df_new_posts.set_index('id', inplace=True)
    #save ids
    pd.concat([existing_posts, df_new_posts]).to_csv(file)
    logger(f"Stored file: {file}", "main")

def save_subreddit(subreddit: SubredditHelper, existing_posts, data_path: str, sorting_options: list, limit=10, min_score=0):
    #Schema for our JSON file
    schema = {
        "subreddit": subreddit.display_name,
        "limit": limit,
        "minimum_score": min_score,
        "sorting_options": sorting_options,
        "posts": []
    }

    new_posts_ids = []
    new_posts_num_comments = []

    # Determine timestamp of crawling start, will be used for composition uid
    crawl_ts = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    for sort in sorting_options:

        # i could pass this as a parameter to avoid this if/else hell but i'm too lazy to find out
        #  if passing subreddit.hot() by parameter will evaluate it before it's submitted
        #  or if it's evaluated inside the pool and not before submission... so i just do an if/else here to be safe
        
        if sort == "hot":
            listing: ListingGenerator = subreddit.hot(limit=limit)
        elif sort == "top":
            listing: ListingGenerator = subreddit.hot(limit=limit)
        elif sort == "new":
            listing: ListingGenerator = subreddit.new(limit=limit)
        elif sort == "controversial":
            listing: ListingGenerator = subreddit.controversial(limit=limit)
        elif sort == "random_rising":
            listing: ListingGenerator = subreddit.random_rising(limit=limit)
        elif sort == "rising":
            listing: ListingGenerator = subreddit.rising(limit=limit)
        else:
            logger("Not supported sorting option", "main")
            continue


        for submission in listing:
            with Lock(): # do we need this? every worker crawls one subreddit at a time, there should be no conflicts?
                exists_in_new = (submission.id in new_posts_ids)
                exists_in_old = (submission.id in existing_posts.index)
                exists = exists_in_new or exists_in_old

            if submission.score >= min_score and not exists:
                logger(f"scrapping submission {submission.id} in subreddit {subreddit.display_name}; num_comments: {submission.num_comments}", "main")
                ss = submission_schema(submission=submission, min_score=min_score)
                schema['posts'].append(ss)
                with Lock():
                    new_posts_ids.append(submission.id)
                    new_posts_num_comments.append(submission.num_comments)


            #if exists and passes certain threshold, remove and add from that file
            if submission.score >= min_score and exists_in_old:
                old_submission = existing_posts.loc[submission.id]
                old_num_comments = old_submission[1]
                old_ts = old_submission[0]

                diff = submission.num_comments - old_num_comments
                if diff > 0.3*old_num_comments:
                    logger(f"for submission {submission.id} in {subreddit.display_name}: more than 30% new comments, refetching submission", "main")
                    # update here
                    file_path = os.path.join(data_path, f"{subreddit.display_name}-{old_ts}.json")
                    
                    with open(file_path, 'r') as f:
                        old_json_submission = json.load(f)
                        to_remove = None
                        #search
                        for post in old_json_submission['posts']:
                            if post['id'] == submission.id:
                                to_remove = post
                                break

                    #remove and add new
                    if to_remove is not None:
                        with open(file_path, 'w') as f:
                            old_json_submission['posts'].remove(to_remove)
                            ss = submission_schema(submission=submission, min_score=min_score)
                            old_json_submission['posts'].append(ss)
                            json.dump(old_json_submission, f, indent=4)

                    #finally, update also the ids file with num_comments
                    #only modify existing_posts, since this will be stored in the end
                    existing_posts.loc[existing_posts.index == submission.id,'num_comments'] = submission.num_comments
                        


    if len(schema['posts']) > 0:
        #save JSON file with posts for that crawl
        file_path = os.path.join(data_path, f"{subreddit.display_name}-{crawl_ts}.json")
        with open(file_path, 'w') as f:
            logger(f"Stored file: {file_path} with {len(schema['posts'])} new posts ", "main")
            json.dump(schema, f, indent=4)
    else:
        logger(f"No new posts for {subreddit.display_name}", "main")

    #save id files (always, bc some posts might have been updated)
    ids_file_path = os.path.join(data_path, f"ids/{subreddit.display_name}.txt")
    store_ids(ids_file_path, existing_posts, crawl_ts, new_posts_ids, new_posts_num_comments)
        


def submission_schema(submission: Submission, min_score=0):
    subreddit: str = submission.subreddit.display_name
    schema = {}
    schema['id'] = submission.id
    schema['title'] = submission.title
    schema['url'] = submission.url
    schema['author'] = submission.author.name if hasattr(submission.author, 'name') else "[deleted]"
    schema['created_utc'] = submission.created_utc
    schema['score'] = submission.score
    schema['num_comments'] = submission.num_comments
    schema['subreddit'] = subreddit
    schema['selftext'] = submission.selftext
    schema['stickied'] = submission.stickied

    schema['comments'] = comments_schema(
        comments=submission.comments,
        context=[submission.title],
        depth=1,
        min_score=min_score)

    return schema


def comments_schema(comments: CommentForest, context, depth=1, min_score=0):
    fetched = []
    comment: Comment
    for comment in comments:
        if isinstance(comment, MoreComments):
            continue
        if comment.score >= min_score:
            if comment.author is not None:
                data = {
                    "id": comment.id,
                    "author": comment.author.name if hasattr(comment.author, 'name') else "[deleted]",
                    "score": comment.score,
                    "created_utc": comment.created_utc,
                    "response": comment.body,
                    "depth": depth,
                    "comments": []
                }

                context.append(comment.body)
                data["comments"] = comments_schema(
                    comments=comment.replies,
                    context=context,
                    depth=depth+1,
                    min_score=min_score)
                context.pop()
                fetched.append(data)
    return fetched


def author_schema(author: Redditor):
    return {
        "author": author.name if hasattr(author, 'name') else "[deleted]",
        "created_utc": author.created_utc,
        "id": author.id,
        "link_karma": author.link_karma,
        "comment_karma": author.comment_karma,
        "is_employee": author.is_employee,
        "has_verified_email": author.has_verified_email
    }


if __name__ == "__main__":
    main()
