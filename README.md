# Reddit Cryptocurrency Analysis

## Description
In this work, we make an attempt to analyse ten cryptocurrency subreddits to yield results and conclusions. We discovered that the discussion in those subreddits attract a long-term attention from different users. Also, individuals tend to gather together with an anchor in a particular subreddit but also spread over the other nine subreddits. Furthermore, there seems to be a correlation between the activity in said subreddits and Bit- coin price movement and we managed to highlight it over a comprehensive process.


## Installation

Install all dependencies using pipenv

```bash
pipenv install
```


## Workflow

### 0. Intro

The workflow of this project consists of three parts, namely:

1. Setup
2. Collecting data (comments, posts) over a time window from different subreddits.
3. Parsing the data into CSVs
4. Doing analysis on the obtained graphs using `networkx`


### 1. Set Up

Before we can scrap, we first need to configure the `.env` file. Here's a template of the needed parameters:

```
REDDIT_USER_AGENT=project:company.com:v1 (by u/USERNNAME)
REDDIT_CLIENT_ID=CLIENT_ID
REDDIT_CLIENT_SECRET=CLIENT_SECRET
REDDIT_CLIENT_USERNAME=USERNAME
REDDIT_CLIENT_PASSWORD=PASSWORD
REDDIT_REFRESH_TOKEN=TOKEN
DATA_PATH=data
LOGS_PATH=data/logs
```

- `REDDIT_USER_AGENT` is the user agent reddit would like to see. According to the PRAW Documentation the provided template is good practice. 
- `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` can be obtained by creating an app on Reddit in the preferences page of your account.
- `REDDIT_CLIENT_USERNAME`, `REDDIT_CLIENT_PASSWORD` self-explanatory.
- `REDDIT_REFRESH_TOKEN` needs to be obtained by following the actions below.
- `DATA_PATH`, `LOGS_PATH` are the paths where the data and logs should be stored. You can either configure them here or set them in the `scrapper.py` file itself.

##### Getting the `REDDIT_REFRESH_TOKEN`
If you don't sign in to Reddit using "2FA" (that's what they call it, even though you just allow the app to access your user profile on Reddit), there might arise authentication issues. To avoid this, it's best practice to get the `REDDIT_REFRESH_TOKEN`. To the the refresh token, one can use the `reddit2fa_connector.py` file. Before running it, create the `.env` file as above but without the `REDDIT_REFRESH_TOKEN`. Then run `python reddit2fa_connector.py` and you should be redirected to your browser where you'll allow the app access. Once you'll alow it, you should automatically be redirected to `localhost:8080`. You'll see the token being displayed in the browser. Copy it and add it to the `.env` file.


### 2. Scraping data from reddit

For the scraping part, there is the `scrapper.py` file. One can configure it by changing the parameters inside the file.

```python
data_path = os.path.join(os.getenv('DATA_PATH'))
logs_path = os.path.join(os.getenv('LOGS_PATH'))
min_score = 3
limit = 1000
sorting_options = ["hot", "top", "new"]
subreddits = ["Bitcoin", "Ethereum", "Dogecoin", "BitcoinBeginners", "CryptoCurrencies", "CryptoTechnology", "CryptoMarkets", "Binance", "CoinBase", "btc"]
```

- `data_path` and `logs_path` should be directories to store the output of the scraping (JSON files) and the logs to check for errors and general state of the software. If you let it be as it is, then you have to specify the paths in your `.env` file.
- `min_score` is the minimum score a comment or post should have to be stored; score = upvotes - downvotes 
- `limit` is the limit of posts that can be fetched from a subreddit (you don't always get 1000 posts for each scraping)
- `sorting_options` a list with elements from `{hot, top, new, controversial, random_rising, rising}`. See PRAW documentation for more information
- `subreddits` list of subreddits to scrap

Now, you should be ready to run the scraping script. If you use Pipenv, run `pipenv python scrapper.py` or enter the Pipenv shell with `pipenv shell` and run `python scrapper.py`.

The scraping will use the `multiprocessing` of python to scrap on each CPU core one subreddit. This will generate a file named for example `Binance-2022-05-04-10-45-32.json`. Be aware that these files will be updated for new comments with time by rerunning the scraper file.

Ideally, you should use a cronjob on the file and run it for example every hour, depending on the information load the subreddits experience each day.


### 3. Parsing the data

The outputted JSON files will contain posts with comments within comments within comments etc. It is basically the same structure one can find on the webpage. To "connect" users and other information with each other and essentially create a data model for the graph, one can use the `csv_dumper.py` class. 

```python 
dp = CSVDumper()
dp.parse_folder('data')
dp.dump_scores('data/csv/scores.csv')
dp.dump_active_subs('data/csv/subs.csv')
dp.dump_edges('data/csv')
```

*Note: When referring to a user and its comments, score etc, we always only consider the comments and scores found in the scraping, not a list of all of their comments ever written on reddit.com or accumulated score.*

Currently it supports

- dumping the cumulated score from the scraped comments for each user;
- dumping a list of subreddits the scraped users commented on; this is is strictly a subset of the list defined in `subreddits`
- dumping the edges in different kind of data models
	- for `deep_link`: Every user that commented on a post gets linked to the author of that post with a weight $\frac{1}{d}$ where $d$ is the depth of the comment, also every user gets linked to every previous author in the comment tree.
	- for `next_link`: Every user that commented on a post gets linked to the author of that post with a weight $\frac{1}{d}$ where $d$ is the depth of the comment, also every user gets linked to only the previous author in the comment tree.
	- for `ucartesian_link`: This connects all users who commented on a post as well as the author of the post in a complete graph. For every post where two users commented on, the edge weight between these two users gets increased by +1.

	
### 4. Analysis

Once the CSV files are dumped, one can do analysis on the data using networkx. Please refer to the notebooks for the analysis.
Also, consider the `algorithms.py` file for our inhouse implementations of PageRank and Louvain.



