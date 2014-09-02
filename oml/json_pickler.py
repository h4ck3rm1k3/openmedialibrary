import json

def loads(*args, **kargs):
    #print('loads', args, kargs)
    if isinstance(args[0], bytes):
        args = (args[0].decode('utf-8'),) + args[1:]
    return json.loads(*args, **kargs)

def dumps(*args, **kargs):
    #print('dumps', args, kargs)
    return json.dumps(*args, **kargs).encode('utf-8')
