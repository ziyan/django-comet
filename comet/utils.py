from . import get_backend

def signal(object_key, events):
    return get_backend().signal(object_key, events)

def register(object_key, token=None):
    return get_backend().register(object_key, token)
