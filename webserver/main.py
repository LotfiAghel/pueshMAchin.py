import os
import json
import time
import asyncio

import tornado.ioloop
import tornado.web
import tornado.websocket
try:
    from . import annotation
except:
    pass
PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH_DIR = os.path.join(PATH, 'static')


class Index(tornado.web.RequestHandler):
    def get(self):
        filename = os.path.join(STATIC_PATH_DIR, 'html/index.html')
        with open(filename) as f:
            content = f.read()
        self.finish(content)


class Index2(tornado.web.RequestHandler):
    def get(self):
        filename = os.path.join(STATIC_PATH_DIR, 'html2/index.html')
        with open(filename) as f:
            content = f.read()
        self.finish(content)


class Annotation(tornado.web.RequestHandler):
    def get(self):
        filename = os.path.join(STATIC_PATH_DIR, 'html/annotation.html')
        with open(filename) as f:
            content = f.read()
        self.finish(content)


class AnnotationApi(tornado.web.RequestHandler):
    def get(self):
        component = self.get_arguments("component")[0]
        station = self.get_arguments("station")[0]
        res = annotation.get(component, station)
        self.write(res)

    def post(self):
        component = self.get_arguments("component")[0]
        station = self.get_arguments("station")[0]
        data = self.request.body
        res = annotation.post(component, station, data)
        self.write(res)


class WebSocket(tornado.websocket.WebSocketHandler):
    async def open(self):
        SYSTEM.register_ws(self)

    def on_message(self, message):
        asyncio.create_task(SYSTEM.message_from_ws(self, json.loads(message)))

    def on_close(self):
        SYSTEM.deregister_ws(self)


class WebSocket2(tornado.websocket.WebSocketHandler):
    import datetime
    data = {
        'status': {
            'main_script': None,  # 'positioning' / 'feed16' / 'empty_rail' / 'main'
            # 'play' / 'pause'
        },
        'recipe': {
            'name': 'Basalin',
            'feed_open': False,
        },
        'errors': [
            {'location_name': 'Station 1', 'message': 'استیشن را خالی کنید - تنظیم هولدر',
                'type': 'error', 'uid': '123', 'clearing': False},
            {'location_name': 'Station 3', 'message': 'استیشن را خالی کنید - تنظیم هولدر',
                'type': 'error', 'uid': '123', 'clearing': True},
            {'location_name': 'Feeder', 'message': 'هولدر نیومده', 'type': 'warning', 'uid': '456'},
        ],
        'stats': {
            'active_batch_no': 'ING0021',
            'counter': 1819,
            'counter_since': (datetime.datetime.now() - datetime.timedelta(hours=2, minutes=30, days=2)).timestamp(),
            'speed': 2315,
            'speed_since': (datetime.datetime.now() - datetime.timedelta(minutes=10)).timestamp()
        }
    }

    async def open(self):
        while True:
            message = self.data
            message = json.dumps(message)
            self.write_message(message)
            await asyncio.sleep(.5)

    def on_message(self, message):
        message = json.loads(message)
        print(message)


def create_server(system=None):
    global SYSTEM
    SYSTEM = system

    app = tornado.web.Application([
        (r"/", Index),
        (r"/annotation", Annotation),
        (r"/annotation/api", AnnotationApi),
        (r"/ws", WebSocket),
        (r'/static/(.*)', tornado.web.StaticFileHandler,
         {'path': STATIC_PATH_DIR}),
        (r'/dataset/(.*)', tornado.web.StaticFileHandler,
         {'path': annotation.DATASET_PATH})
    ], debug=True)
    app.listen(8080)


def test_server(system=None):
    app = tornado.web.Application([
        (r"/", Index2),
        (r"/ws", WebSocket2),
        (r'/static/(.*)', tornado.web.StaticFileHandler,
         {'path': STATIC_PATH_DIR}),
    ], debug=True)
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    test_server()
    while True:
        time.sleep(1)
