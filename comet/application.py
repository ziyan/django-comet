from django.core.servers.basehttp import get_internal_wsgi_application
from handlers import AjaxHandler, WebSocketHandler, RpcHandler
import tornado.web
import tornado.wsgi

class Application(tornado.web.Application):

    def __init__(self, is_comet=True, is_django=True):
        handlers = []
        if is_comet:
            handlers += self.get_comet_handlers()
        if is_django:
            handlers += self.get_django_handlers()
        tornado.web.Application.__init__(self, handlers)

    def get_comet_handlers(self):
        handlers = [
            (r'/comet/ajax/', AjaxHandler),
            (r'/comet/websocket/', WebSocketHandler),
            (r'/comet/rpc/', RpcHandler),
        ]
        return handlers

    def get_django_handlers(self):
        django_application = get_internal_wsgi_application()
        django_wsgi = tornado.wsgi.WSGIContainer(django_application)
        handlers = [
            (
                r'.*',
                tornado.web.FallbackHandler,
                dict(fallback=django_wsgi)
            ),
        ]
        return handlers

