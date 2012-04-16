backend = None

def get_backend():
    global backend

    if not backend:
        from backends import TornadoCometBackend
        backend = TornadoCometBackend()

    return backend
