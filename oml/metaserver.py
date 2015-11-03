# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

import oxtornado
from oxtornado import actions

import meta
import utils

import logging
logger = logging.getLogger('metaoml')
logging.basicConfig(level=logging.DEBUG)

def findMetadata(data):
    '''
        takes {
            query: string,
        }
        returns {
            items: [{
                key: value
            }]
        }
        key is one of the supported identifiers: isbn, olid...
    '''
    response = {}
    logger.debug('findMetadata %s', data)
    response['items'] = meta.find(data['query'])
    return response
actions.register(findMetadata)

def getMetadata(data):
    '''
        takes {
            key: value
            includeEdits: boolean
        }
        key can be one of the supported identifiers: isbn, oclc, olid,...
    '''
    logger.debug('getMetadata %s', data)
    if 'includeEdits' in data:
        include_edits = data.pop('includeEdits')
    else:
        include_edits = False
    key, value = next(iter(data.items()))
    if key == 'isbn':
        value = utils.normalize_isbn(value)
    logger.debug('getMetadata key=%s value=%s', key, value)
    response = meta.lookup(key, value)
    if response:
        response['primaryid'] = [key, value]
    return response
actions.register(getMetadata)

def run():

    options = {
        'debug': True
    }

    handlers = [
        (r'/api/', oxtornado.ApiHandler),
    ]

    http_server = HTTPServer(Application(handlers, **options))

    port = 9855
    address = ''
    http_server.listen(port, '')

    main = IOLoop.instance()

    if ':' in address:
        host = '[%s]' % address
    elif not address:
        host = '[::1]'
    else:
        host = address
    url = 'http://%s:%s/' % (host, port)
    print(url)
    main.start()

if __name__ == '__main__':
    run()
