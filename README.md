# Social Media Analytics

## Project Description

The goal of this project is to perform sentimental analysis (SA) in real time
on cryptocurrencies. For that purpose, Twitter is taken as a network source
both to discover communities centered around cryptocurrencies and to retrieve
text data for SA itself. Influencer accounts (e.g. @Bitcoin, @ethereum,
@BTCTN,etc.) as well as hashtags are taken as starting points to build the
network and the analysis. SA would be done both inside and outside communities
to deviate correlation and interesting results. Furthermore, SA would be
multidimensional with respect to time, so that it could be compared with
cryptocurrencies' rates. Consequently, the end result would most likely be the
currencies' rates with key points (e.g. extrema) that could reveal both SA (in-
and outside communities).


## Installation

Install all dependencies using pipenv

```bash
pipenv install
```


## Workflow

### 0. Intro

The workflow of this project consists of three parts, namely:

0. Setup
1. Scrapping comments over a time window from different subreddits.
2. Parsing the comments into CSVs
3. Doing analysis on the obtained graphs using `networkx`


### 1. Set Up

Before we can scrap, we first need to configure the `.env` file. Here's a template of the needed parameters:

```
REDDIT_USER_AGENT=project:company.com:v1 (by u/USERNNAME)
REDDIT_CLIENT_ID=CLIENT_ID
REDDIT_CLIENT_SECRET=CLIENT_SECRET
REDDIT_CLIENT_USERNAME=USERNAME
REDDIT_CLIENT_PASSWORD=PASSWORD
REDDIT_REFRESH_TOKEN=TOKEN
```

- `REDDIT_USER_AGENT` is the user agent reddit would like to see. According to the PRAW Documentation the provided template is good practice. 
- `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` can be obtained by creating an app on Reddit in the preferences page of your account.
- `REDDIT_CLIENT_USERNAME`, `REDDIT_CLIENT_PASSWORD` self-explanatory.
- `REDDIT_REFRESH_TOKEN` needs to be obtained by following the actions below.

These environment variables should be loaded with the script. If you use pipenv, it will automatically do this for you. Otherwise you might need to source this file where you export each variable using something like `xargs`.

##### Getting the `REDDIT_REFRESH_TOKEN`
If you don't sign in to Reddit using "2FA" (that's what they call it, even though you just allow the app to access your user profile on Reddit), there might arise authentication issues. To avoid this, it's best practice to get the `REDDIT_REFRESH_TOKEN`. To the the refresh token, one can use the `reddit2fa_connector.py` file. Before running it, create the `.env` file as above but without the `REDDIT_REFRESH_TOKEN`. Then run `python reddit2fa_connector.py` and you should be redirected to your browser where you'll allow the app access. Once you'll alow it, you should automatically be redirected to `localhost:8080`. You'll see the token being displayed in the browser. Copy it and add it to the `.env` file.


### 2. Scrapping data from reddit

For the scrapping part, there is the `scrapper.py` file. One can configure it by changing the parameters inside the file.

```python
data_path = os.path.join("data")
logs_path = os.path.join("data/logs")
min_score = 3
limit = 1000
sorting_options = ["hot", "top", "new"]
subreddits = ["Bitcoin", "Ethereum", "Dogecoin", "BitcoinBeginners", "CryptoCurrencies", "CryptoTechnology", "CryptoMarkets", "Binance", "CoinBase", "btc"]
```

- `data_path` and `logs_path` should be directories to store the output of the scrapping (JSON files) and the logs to check for errors and general state of the software
- `min_score` is the minimum score a comment or post should have to be stored; score = upvotes - downvotes 
- `limit` is the limit of posts that can be fetched from a subreddit (you don't always get 1000 posts for each scrapping)
- `sorting_options` a list with elements from `{hot, top, new, controversial, random_rising, rising}`. See PRAW documentation for more information
- `subreddits` list of subreddits to scrap

Now, you should be ready to run `python scrapper.py`. 

The scrapping will use the `multiprocessing` of python to scrap on each CPU core one subreddit. This will generate a file named for example `Binance-2022-05-04-10-45-32.json`. Be aware that these files will be updated for new comments with time by rerunning the scrapper file.

Ideally, you should use a cronjob on the file and run it for example every hour, depending on the information load the subreddits experience each day.


### 3. Parsing the data

The outputted JSON files will contain posts with comments within comments within comments etc. It basically is the same structure one can find on the webpage. To "connect" users and other information with each other and essentially create a data model for the graph, one can use the `csv_dumper.py` class. 

```python 
dp = CSVDumper()
dp.parse_folder('data')
dp.dump_scores('data/csv/scores.csv')
dp.dump_active_subs('data/csv/subs.csv')
dp.dump_edges('data/csv')
```

*Note: When refering to a user and its comments, score etc, we always only consider the comments and scores found in the scrapping, not a list of all of their comments ever written on reddit.com or accumulated score.*

Currently it supports

- dumping the cumulated score from the scrapped comments for each user;
- dumping a list of subreddits the scrapped users commented on; this is is strictly a subset of the list defined in `subreddits`
- dumping the edges in different kind of data models
	- for `deep_link`: Every user that commented on a post gets linked to the author of that post with a weight $\frac{1}{d}$ where $d$ is the depth of the comment, also every user gets linked to every previous author in the comment tree.
	- for `next_link`: Every user that commented on a post gets linked to the author of that post with a weight $\frac{1}{d}$ where $d$ is the depth of the comment, also every user gets linked to only the previous author in the comment tree.
	- for `ucartesian_link`: This connects all users who commented on a post as well as the author of the post in a complete graph. For every post where two users commented on, the edge weight between these two users gets increased by +1.

	
### 4. Analysis

Once the CSV files are dumped, one can do analysis on the data using networkx.



