import pdf
import epub
import txt
import os
import base64
import ox

def get_id(f):
    return base64.b32encode(ox.sha1sum(f).decode('hex'))

def metadata(f):
    ext = f.split('.')[-1]
    data = {}
    if ext == 'pdf':
        info = pdf.info(f)
    elif ext == 'epub':
        info = epub.info(f)
    elif ext == 'txt':
        info = txt.info(f)

    for key in ('title', 'author', 'date', 'publisher', 'isbn'):
        if key in info:
            value = info[key]
            if isinstance(value, str):
                try:
                    value = value.decode('utf-8')
                except:
                    value = None
            if value:
                data[key] = info[key]

    if 'isbn' in data:
        value = data.pop('isbn')
        if len(value) == 10:
            data['isbn10'] = value
            data['mainid'] = 'isbn10'
        else:
            data['isbn13'] = value
            data['mainid'] = 'isbn13'
    if not 'title' in data:
        data['title'] = os.path.splitext(os.path.basename(f))[0]
    if 'author' in data and isinstance(data['author'], basestring):
        data['author'] = [data['author']]
    return data

