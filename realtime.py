#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
import requests
import time
import database
import datetime
import ConfigParser
from bs4 import BeautifulSoup as bs
import json
import os
import base64
import logging
from logging.handlers import TimedRotatingFileHandler


class Realtime(object):

    def __init__(self, config_file):
        self.__url = 'http://realtime.search.yahoo.co.jp/search?p=simeji&ei=UTF-8'
        self.__last_tweet_id = None
        self.__db = database.Database(config_file)
        self.__db.connect()
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        self.__init_log(config)

    def __init_log(self, config):
        store_path = config.get('query', 'store_path')
        try:
            os.mkdir(store_path)
        except OSError:
            pass

        file_path = config.get('query', 'file_path')

        file_handler = TimedRotatingFileHandler(file_path, 'D', 1, 0)
        file_handler.suffix = '%Y%m%d'
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        self.__logger = logging.getLogger('twitter')
        self.__logger.addHandler(file_handler)

    def request(self):
        r = requests.get(self.__url)
        if r.status_code == 200:
            soup = bs(r.text)
            it = soup.find('div', {'class': 'cnt cf'})
            while it:
                try:
                    author, tweet_id, tweet_time, text, with_refs = self.analysis(it)
                    if self.__last_tweet_id == tweet_id:  # 当前这条已存储，前面的也不需要了
                        break
                    else:
                        json_dumps = {
                            'tweet_id': tweet_id,
                            'author': author,
                            'tweet_time': tweet_time,
                            'text': text,
                        }
                        self.__logger.critical(json.dumps(json_dumps))
                        if with_refs:
                            text = base64.b64encode(text.encode("utf-8"))
                            self.__db.add_tweet(tweet_id, author, text, tweet_time)

                        self.__last_tweet_id = tweet_id
                except Exception as e:
                    self.__logger.fatal(str(e))
                finally:
                    it = it.find_next('div', {'class': 'cnt cf'})

    def analysis(self, it):
        timestamp = it.get('data-time')
        tweet_time = datetime.datetime.utcfromtimestamp(int(timestamp))
        tweet_time = tweet_time.strftime("%Y-%m-%d %H:%M:%S")
        text = it.h2.text
        refs = it.h2.find('a')
        with_refs = False
        if refs and refs.getText()[0] == '@':
            with_refs = True
        author = it.find('a', {'class': 'nam'})
        source = author.find_next('a', {'target': '_blank'})
        author = author.getText()
        source = source.get('href')
        tweet_id = source.rsplit("/", 1)[-1]
        tweet_id = int(tweet_id)
        return author, tweet_id, tweet_time, text, with_refs

    def run(self):
        while 1:
            self.request()
            time.sleep(5)


if __name__ == '__main__':
    import sys
    rt = Realtime(sys.argv[1])
    rt.run()
