#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
import MySQLdb
import ConfigParser
import datetime


class Database(object):

    def __init__(self, config_file):
        self.__config = ConfigParser.ConfigParser()
        self.__config.read(config_file)
        self.__conn = None

    def __del__(self):
        if self.__conn:
            self.__conn.close()

    def connect(self):
        host = self.__config.get('mysql', 'host')
        user = self.__config.get('mysql', 'user')
        passwd = self.__config.get('mysql', 'passwd')
        port = self.__config.getint('mysql', 'port')
        db = self.__config.get('mysql', 'db')
        self.__conn = MySQLdb.connect(
            host=host,
            user=user,
            passwd=passwd,
            db=db,
            port=port,
        )

    def create_table(self):
        with self.__conn:
            cur = self.__conn.cursor()
            table = self.__config.get('mysql', 'table')
            sql = """CREATE TABLE IF NOT EXISTS `{table}` (
                `tweet_id` VARCHAR(20) NOT NULL PRIMARY KEY,
                `author_id` VARCHAR(12) NOT NULL,
                `text` TEXT NOT NULL,
                `tweet_time` DATETIME NOT NULL,
                `db_time` DATETIME NOT NULL
                )""".format(table=table)
            cur.execute(sql)

    def add_tweet(self, tweet_id, author_id, text, tweet_time):
        with self.__conn:
            db_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            cur = self.__conn.cursor()
            table = self.__config.get('mysql', 'table')
            value_list = ', '.join(["'{}'".format(x) for x in [tweet_id,
                author_id, text, tweet_time, db_time]])
            where_list = "`tweet_id` = '{}'".format(tweet_id)

            sql = """INSERT INTO {table}
                (`tweet_id`, `author_id`, `text`, `tweet_time`, `db_time`)
                SELECT {value_list} FROM DUAL WHERE NOT EXISTS (SELECT * FROM
                {table} WHERE {where_list})""".format(
                    table=table,
                    value_list=value_list,
                    where_list=where_list,
                )
            cur.execute(sql)

    def count_tweet(self, date_beg, date_end):
        with self.__conn:
            try:
            cur = self.__conn.cursor()
            except:
                self.connect()
                cur = self.__conn.cursor()
            table = self.__config.get('mysql', 'table')
            sql = """SELECT COUNT(*) FROM {table} WHERE `tweet_time` >=
                '{date_beg}' AND `tweet_time` < '{date_end}'""".format(
                table=table, date_beg=date_beg, date_end=date_end)
            cur.execute(sql)
            item = cur.fetchone()
            count = item[0]
        return count
