#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
import oauth2 as oauth
import ConfigParser
import urllib
import time
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import database
import base64
import datetime


class Twitter(object):

    def __init__(self, config_file):
        self.__db = database.Database(config_file)
        config = ConfigParser.RawConfigParser()

        # initilize twitter client
        config.read(config_file)
        consumer = oauth.Consumer(
            key=config.get('auth', 'consumer_key'),
            secret=config.get('auth', 'consumer_secret'),
        )
        token = oauth.Token(
            key=config.get('auth', 'access_token_key'),
            secret=config.get('auth', 'access_token_secret'),
        )
        self.__client = oauth.Client(consumer, token)

        # adjust query frequence
        qpm = config.getint('query', 'query_per_minute')
        self.__spq = 60.0 / qpm  # second per query

        # initilize store path & files
        self.__init_log(config)

    def __init_log(self, config):
        store_path = config.get('query', 'store_path')
        os.mkdir(store_path)
        file_path = config.get('query', 'file_path')

        file_handler = TimedRotatingFileHandler(file_path, 'D', 1, 0)
        file_handler.suffix = '%Y%m%d'
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        self.__logger = logging.getLogger('twitter')
        self.__logger.addHandler(file_handler)

    def __make_url(self, url, params):
        url = "{}?{}".format(url, urllib.urlencode(params))
        return url

    def search(self, query, since_id=None):
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        params = {
            'q': query,
            'count': 100,
            'lang': 'ja',
        }
        if since_id is not None:
            params['since_id'] = since_id
        url = self.__make_url(url, params)

        resp, content = self.__client.request(url, method='GET')
        if resp['status'] != '200':
            return None
        return content

    def run(self, query):
        since_id = None
        while 1:
            try:
                beg_time = time.time()
                content = self.search(query, since_id)
                if content is None:
                    time.sleep(self.__spq * 3)
                cj = json.loads(content)
                for index, tweet in enumerate(cj['statuses']):
                    if index == 0:
                        since_id = tweet['id']

                    # store in database
                    text = tweet['text'].encode("utf-8")
                    text = base64.b64encode(text)
                    tweet_id = tweet['id_str']
                    author_id = tweet['user']['id_str']
                    tweet_time = tweet['created_at'].replace(" +0000", "")
                    tweet_time = datetime.datetime.strptime(tweet_time, "%c")
                    try:
                        at_list = tweet['entities']['user_mentions']
                        num_at = len(at_list)
                    except KeyError:
                        num_at = 0

                    if num_at > 0:
                        self.__db.add_tweet(tweet_id, author_id, text, tweet_time)

                    # store in file
                    json_tweet = json.dumps(tweet)
                    self.__logger.critical(json_tweet)
                time_elapsed = (time.time() - beg_time)
                if time_elapsed < self.__spq:
                    time.sleep(self.__spq - time_elapsed)
            except:
                time.sleep(self.__spq * 10)


if __name__ == '__main__':
    import sys
    twitter = Twitter(sys.argv[1])
    twitter.run('simeji')
