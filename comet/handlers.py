from tornadorpc import async, private
from tornadorpc.xml import XMLRPCHandler
from tornado.web import asynchronous
import logging
import tornado.ioloop
import tornado.web
import tornado.websocket
import brukva
import redis
import simplejson

class SignalMixin(object):
    TOKEN_PREFIX = 'comet.token.'
    EVENT_PREFIX = 'comet.event.'
    CHANNEL_PREFIX = 'comet.channel.'
    TOKEN_TTL = 15 * 60

    callbacks = dict()
    api = None
    listener = None

    def _wait(self, token, cookie, callback):
        cls = SignalMixin

        # initialize redis
        if not cls.api:
            cls.api = redis.StrictRedis()

        if not cls.listener:
            cls.listener = brukva.Client()
            cls.listener.psubscribe(cls.CHANNEL_PREFIX + '*')
            cls.listener.listen(self._signal)

        # try to find the token
        object_key = cls.api.get(cls.TOKEN_PREFIX + token)
        if not object_key:
            return False

        # update token expiry
        cls.api.expire(cls.TOKEN_PREFIX + token, cls.TOKEN_TTL)

        # try to find to see if there is any event already
        event_keys = cls.api.keys(cls.EVENT_PREFIX + object_key + '.*')
        filtered_event_keys = []
        filtered_event_ids = []

        for event_key in event_keys:
            event_id = int(event_key.rsplit('.', 1)[1])
            if event_id > cookie:
                filtered_event_keys.append(event_key)
                filtered_event_ids.append(event_id)

        # get the list of events in one go and calculate new cookie
        events = []
        cookie = 0
        if filtered_event_keys:
            filtered_events = cls.api.mget(filtered_event_keys)
            for event_id, event in zip(filtered_event_ids, filtered_events):
                if event:
                    events.append(simplejson.loads(event))
                    if event_id > cookie:
                        cookie = event_id

        # early return to caller
        if events:
            return {
                'cookie': cookie,
                'events': events,
            }

        # register callback
        callbacks = []
        if object_key in cls.callbacks:
            callbacks = cls.callbacks[object_key]
        if not callback in callbacks:
            callbacks.append(callback)
        cls.callbacks[object_key] = callbacks
        return None

    def _cancel(self, callback):
        cls = SignalMixin

        obsolete_objects = []

        for object_key, callbacks in cls.callbacks.iteritems():
            if callback not in callbacks:
                continue
            callbacks.remove(callback)
            if callbacks:
                cls.callbacks[object_key] = callbacks
                continue
            obsolete_objects.append(object_key)

        # remove empty callback list for some objects
        for object_key in obsolete_objects:
            del cls.callbacks[object_key]

    def _signal(self, message):
        cls = SignalMixin

        object_key = message.pattern[len(cls.CHANNEL_PREFIX):]
        if not object_key in cls.callbacks:
            return

        data = simplejson.loads(message.body)

        callbacks = cls.callbacks[object_key]
        obsolete_callbacks = []

        for callback in callbacks:
            try:
                if not callback(data):
                    obsolete_callbacks.append(callback)
            except:
                logging.error('Error in waiter callback', exc_info=True)

        for callback in obsolete_callbacks:
            callbacks.remove(callback)

        if callbacks:
            cls.callbacks[object_key] = callbacks
        else:
            del cls.callbacks[object_key]

class AjaxHandler(tornado.web.RequestHandler, SignalMixin):
    @asynchronous
    def post(self):
        token = self.get_argument('token')
        cookie = int(self.get_argument('cookie', 0))
        data = self._wait(token, cookie, self.on_signal)
        if data is False:
            raise tornado.web.HTTPError(403)
        elif data:
            self.set_header('Access-Control-Allow-Origin', '*')
            self.set_header('Access-Control-Allow-Methods', 'POST')
            self.set_header('Access-Control-Allow-Headers', '*')
            self.finish(data)

    def on_signal(self, data):
        if not self.request.connection.stream.closed():
            self.set_header('Access-Control-Allow-Origin', '*')
            self.set_header('Access-Control-Allow-Methods', 'POST')
            self.set_header('Access-Control-Allow-Headers', '*')
            self.finish(data)
        return False

    def on_connection_close(self):
        self._cancel(self.on_signal)

class WebSocketHandler(tornado.websocket.WebSocketHandler, SignalMixin):
    def open(self):
        token = self.get_argument('token')
        cookie = int(self.get_argument('cookie', 0))
        data = self._wait(token, cookie, self.on_signal)
        if data is False:
            self.close()
        elif data:
            self.write_message(data)

    def on_signal(self, data):
        self.write_message(data)
        return True

    def on_close(self):
        self._cancel(self.on_signal)

class RpcHandler(XMLRPCHandler, SignalMixin):

    @async
    def wait(self, token, cookie=0):
        data = self._wait(token, cookie, self.on_signal)
        if data is False:
            raise Exception('Invalid token.')
        elif data:
            self.result(data)

    @private
    def on_signal(self, data):
        if not self.request.connection.stream.closed():
            self.result(data)
        return False

    @private
    def on_connection_close(self):
        self._cancel(self.on_signal)
