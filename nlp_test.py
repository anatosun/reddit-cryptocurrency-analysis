import os
import json
import re, string, random
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import twitter_samples, stopwords
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk import classify, NaiveBayesClassifier

# Install first within the python interpreter
'''
import nltk
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('vader_lexicon')
'''

def remove_noise(tweet_tokens, stop_words = ()):
   cleaned_tokens = []

   for token, tag in pos_tag(tweet_tokens):
      token = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|'\
                     '(?:%[0-9a-fA-F][0-9a-fA-F]))+','', token)
      token = re.sub("(@[A-Za-z0-9_]+)","", token)

      if tag.startswith("NN"):
         pos = 'n'
      elif tag.startswith('VB'):
         pos = 'v'
      else:
         pos = 'a'

      lemmatizer = WordNetLemmatizer()
      token = lemmatizer.lemmatize(token, pos)

      if len(token) > 0 and token not in string.punctuation and token.lower() not in stop_words:
         cleaned_tokens.append(token.lower())
   return cleaned_tokens

def get_all_words(cleaned_tokens_list):
   for tokens in cleaned_tokens_list:
      for token in tokens:
         yield token

def get_tweets_for_model(cleaned_tokens_list):
   for tweet_tokens in cleaned_tokens_list:
      yield dict([token, True] for token in tweet_tokens)

def get_classifier_tuto_1():
   # See: https://www.digitalocean.com/community/tutorials/how-to-perform-sentiment-analysis-in-python-3-using-the-natural-language-toolkit-nltk
   
   print("Train classifier with tweets...")

   stop_words = stopwords.words('english')

   positive_tweet_tokens = twitter_samples.tokenized('positive_tweets.json')
   negative_tweet_tokens = twitter_samples.tokenized('negative_tweets.json')

   positive_cleaned_tokens_list = []
   negative_cleaned_tokens_list = []

   for tokens in positive_tweet_tokens:
      positive_cleaned_tokens_list.append(remove_noise(tokens, stop_words))

   for tokens in negative_tweet_tokens:
      negative_cleaned_tokens_list.append(remove_noise(tokens, stop_words))

   positive_tokens_for_model = get_tweets_for_model(positive_cleaned_tokens_list)
   negative_tokens_for_model = get_tweets_for_model(negative_cleaned_tokens_list)

   positive_dataset = [(tweet_dict, "Positive")
                        for tweet_dict in positive_tokens_for_model]

   negative_dataset = [(tweet_dict, "Negative")
                        for tweet_dict in negative_tokens_for_model]

   dataset = positive_dataset + negative_dataset

   random.shuffle(dataset)

   train_data = dataset[:7000]
   test_data = dataset[7000:]

   classifier = NaiveBayesClassifier.train(train_data)

   print(classifier.show_most_informative_features(10))

   print("Accuracy is:", classify.accuracy(classifier, test_data), "\n")

   return classifier
   
def add_sentiment_analysis_to_file(file_name, sa_function):
   print(f"Update {file_name} with sentiment analysis...")

   file = os.path.join('data', file_name)
   new_file = os.path.join('data', file_name.split(".")[0] + "-sa.json")

   with open(file, 'r') as f:
      subreddit = json.load(f)
      for post in subreddit['posts']:
         text = post['text'] if post['text'] else post['title']
         post['sentiment_analysis'] = sa_function(text)
         recursive_comment_update(post, sa_function)

   with open(new_file, 'w') as f:
      json.dump(subreddit, f, indent=4)      

def recursive_comment_update(post, sa_function):
   if post['comments']:
      for comment in post['comments']:
         text = comment['response']
         comment['sentiment_analysis'] = sa_function(text)
         recursive_comment_update(comment, sa_function)

if __name__ == "__main__":
   classifier = get_classifier_tuto_1()

   sa_tuto_1 = lambda text: classifier.classify(dict([token, True] for token in remove_noise(word_tokenize(text))))
   
   # Update all files with sentiment analysis
   '''
   for file in os.listdir(os.path.join('data')):
      if file.endswith(".json"):
         add_sentiment_analysis_to_file(file, sa_tuto_1)
   '''