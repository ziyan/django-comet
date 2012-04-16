from . import get_backend

def signal_object(obj, events):
    return get_backend().signal(obj, events)

def register_object(obj, token=None):
    return get_backend().register(obj, token)
