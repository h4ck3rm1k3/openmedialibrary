import json

def loads(*args, **kwargs):
    #print('loads', args, kwargs)
    if isinstance(args[0], bytes):
        args = (args[0].decode('utf-8'),) + args[1:]
    return json.loads(*args, **kwargs)

def dumps(*args, **kwargs):
    #print('dumps', args, kwargs)
    return json.dumps(*args, **kwargs).encode()
