#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
import tornado.ioloop
import tornado.web
import tornado.autoreload
import database
import json
import datetime
import sys


db = database.Database(sys.argv[1])
db.connect()

class ApiCount(tornado.web.RequestHandler):

    def get(self):
        errno = 0
        count_data = None
        try:
            beg_date = self.get_argument("beg_date", None)
            end_date = self.get_argument("end_date", None)
            beg_date = datetime.datetime.strptime(beg_date, "%m/%d/%Y")
            end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y")
            count_data = self.__count_per_day(beg_date, end_date)
        except Exception as e:
            errno = 1
            count_data = str(e)
        finally:
            ret_json = {
                'errno': errno,
                'data': count_data,
            }
            self.write(json.dumps(ret_json))

    def __count_per_day(self, beg_date, end_date):
        delta = datetime.timedelta(days=1)
        cur_date = beg_date
        count_list = []
        label_list = []
        while cur_date < end_date:
            count = db.count_tweet(
                cur_date.strftime("%Y-%m-%d %H:%M:%S"),
                (cur_date + delta).strftime("%Y-%m-%d %H:%M:%S")
            )
            label_list.append(cur_date.strftime("%Y-%m-%d"))
            count_list.append(count)
            cur_date += delta
        return {'labels': label_list, 'counts': count_list}


class WebCount(tornado.web.RequestHandler):

    def get(self):
        self.render('templates/count.html')


if __name__ == '__main__':
    application = tornado.web.Application([
        (r'/api/count', ApiCount),
        (r'/count', WebCount),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {"path":"static"}),
    ])
    port = 8086
    application.listen(port)
    instance = tornado.ioloop.IOLoop.instance().start()
    tornado.autoreload.start(instance)
    instance.start()
