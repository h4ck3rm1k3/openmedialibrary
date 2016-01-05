from ox.cache import read_url
from ox import decode_html, strip_tags, find_re
import json
import re
from urllib.parse import unquote
import lxml.html
import stdnum.isbn

def info(key, value):
    if key not in ('isbn',):
        raise IOError('unknwon key %s' % key)
    if len(value) == 13:
        value = stdnum.isbn.to_isbn10(value)
    if len(value) != 10:
        raise IOError('invalid isbn %s' % value)

    url = 'http://www.amazon.com/dp/' + value
    data = read_url(url).decode()
    doc = lxml.html.document_fromstring(data)
    info = {}
    if '<title>404 - Document Not Found</title>' in data:
        return info
    for l in doc.xpath('//link[@rel="canonical" and @href]'):
        info['asin'] = [l.get('href').rpartition('/')[-1]]
        break
    info['title'] = strip_tags(decode_html(doc.xpath('//span[@id="productTitle"]')[0].text))
    info['description'] = strip_tags(decode_html(unquote(re.compile('encodedDescription\' : "(.*?)",').findall(data)[0])))
    content = doc.xpath('//div[@class="content"]')[0]
    content_info = {}
    for li in content.xpath('.//li'):
        v = li.text_content()
        if ': ' in v:
            k, v = li.text_content().split(': ', 1)
            content_info[k.strip()] = v.strip()
    if 'Language' in content_info:
        info['language'] = content_info['Language']
    if 'Publisher' in content_info:
        if ' (' in content_info['Publisher']:
            info['date'] = find_re(content_info['Publisher'].split(' (')[-1], '\d{4}')
        info['publisher'] = content_info['Publisher'].split(' (')[0]
        if '; ' in info['publisher']:
            info['publisher'], info['edition'] = info['publisher'].split('; ', 1)

    if 'ISBN-13' in content_info:
        if not 'isbn' in info: info['isbn'] = []
        info['isbn'].append(content_info['ISBN-13'].replace('-', ''))
    if 'ISBN-10' in content_info:
        if not 'isbn' in info: info['isbn'] = []
        info['isbn'].append(content_info['ISBN-10'])

    a = doc.xpath('//span[@class="a-size-medium"]')
    if a:
        for span in a:
            r = span.getchildren()[0].text.strip()
            if 'Translator' in r:
                role = 'translator'
            else:
                role = 'author'
            if not role in info: info[role] = []
            info[role].append(span.text.strip())
    else:
        for span in doc.xpath('//span[@class="author notFaded"]'):
            author = [x.strip() for x in span.text_content().strip().split('\n') if x.strip()]
            if 'Translator' in author[-1]:
                role = 'translator'
            else:
                role = 'author'
            if not role in info: info[role] = []
            info[role].append(author[0])

    covers = re.compile('data-a-dynamic-image="({.+?})"').findall(data)[0]
    covers = json.loads(decode_html(covers))
    last = [0,0]
    for url in covers:
        if covers[url] > last:
            last = covers[url]
            info['cover'] = re.sub('(\._SX.+?_\.)', '.', url)
    return info
