from django.utils import simplejson
from collections import Iterable
import redis
import hashlib
import uuid

class TornadoCometBackend(object):
    OBJECT_PREFIX = 'comet.object.'
    TOKEN_PREFIX = 'comet.token.'
    EVENT_PREFIX = 'comet.event.'
    CHANNEL_PREFIX = 'comet.channel.'
    TOKEN_TTL = 15 * 60
    EVENT_TTL = 10

    def __init__(self):
        self.api = redis.StrictRedis()

    def signal(self, obj, events):
        cls = TornadoCometBackend
        object_key = self._get_object_key(obj)
        cookie = 0

        if not isinstance(events, Iterable):
            events = [events]

        for event in events:
            # figure out event id to use
            cookie = self.api.incr(cls.OBJECT_PREFIX + object_key)

            # save event in redis with expiry
            event_key = object_key + '.' + str(cookie)
            if not self.api.setnx(cls.EVENT_PREFIX + event_key, simplejson.dumps(event)):
                raise Exception('Duplicate event key %s.' % event_key)
            self.api.expire(cls.EVENT_PREFIX + event_key, cls.EVENT_TTL)

        # publish event to subscribers
        data = simplejson.dumps({
            'cookie': cookie,
            'events': events,
        })

        if self.api.publish(cls.CHANNEL_PREFIX + object_key, data):
            return True

        return False

    def register(self, obj, token=None):
        cls = TornadoCometBackend
        object_key = self._get_object_key(obj)

        if token and self.api.get(cls.TOKEN_PREFIX + token) == object_key:
            self.api.expire(cls.TOKEN_PREFIX + token, cls.TOKEN_TTL)
            return token

        for unused_trial in range(1000):
            token = hashlib.sha256(object_key + '.' + str(uuid.uuid4())).hexdigest()
            if self.api.setnx(cls.TOKEN_PREFIX + token, object_key):
                self.api.expire(cls.TOKEN_PREFIX + token, cls.TOKEN_TTL)
                return token

        raise Exception('Failed to generate a unique token.')

    def _get_object_key(self, obj):
        return obj.object_type() + '.' + obj.uuid
