

def normalize_isbn(value):
    return ''.join([s for s in value if s.isdigit() or s == 'X'])

