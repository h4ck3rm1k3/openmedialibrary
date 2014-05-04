
def get_by_key(objects, key, value):
    obj = filter(lambda o: o.get(key) == value, objects)
    return obj and obj[0] or None

def get_by_id(objects, id):
    return get_by_key(objects, 'id', id)

