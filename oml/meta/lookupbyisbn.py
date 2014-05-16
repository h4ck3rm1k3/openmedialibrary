from ox.cache import read_url
from ox import find_re, strip_tags, decode_html
import re
import stdnum.isbn

base = 'http://www.lookupbyisbn.com'

def get_ids(key, value):
    ids = []
    if key in ('isbn10', 'isbn13', 'asin'):
        url = '%s/Search/Book/%s/1' % (base, value)
        data = read_url(url).decode('utf-8')
        m = re.compile('href="(/Lookup/Book/[^"]+?)"').findall(data)
        if m:
            asin = m[0].split('/')[-3]
            ids.append(('asin', asin))
    if key == 'isbn10':
        ids.append(('isbn13', stdnum.isbn.to_isbn13(value)))
    if key == 'asin':
        if stdnum.isbn.is_valid(value):
            ids.append(('isbn10', value))
    if ids:
        print 'lookupbyisbn.get_ids', key, value
        print ids
    return ids

def lookup(id):
    print 'lookupbyisbn.lookup', id
    r = {
        'asin': id
    }
    url = '%s/Lookup/Book/%s/%s/1' % (base, id, id)
    data = read_url(url).decode('utf-8')
    r["title"] = find_re(data, "<h2>(.*?)</h2>")
    keys = {
        'author': 'Author(s)',
        'publisher': 'Publisher',
        'date': 'Publication date',
        'edition': 'Edition',
        'binding': 'Binding',
        'volume': 'Volume(s)',
        'pages': 'Pages',
    }
    for key in keys:
        r[key] = find_re(data, '<span class="title">%s:</span>(.*?)</li>'% re.escape(keys[key]))
        if r[key] == '--':
            r[key] = ''
        if key == 'pages' and r[key]:
            r[key] = int(r[key])
    desc = find_re(data, '<h2>Description:<\/h2>(.*?)<div ')
    desc = desc.replace('<br /><br />', ' ').replace('<br /> ', ' ').replace('<br />', ' ')
    r['description'] = decode_html(strip_tags(desc))
    r['cover'] = find_re(data, '<img src="(.*?)" alt="Book cover').replace('._SL160_', '')
    for key in r:
        if isinstance(r[key], basestring):
            r[key] = decode_html(strip_tags(r[key])).strip()
    if 'author' in r and isinstance(r['author'], basestring) and r['author']:
        r['author'] = [r['author']]
    else:
        r['author'] = []
    if r['description'].lower() == u'Description of this item is not available at this time.'.lower():
        r['description'] = ''
    return r

