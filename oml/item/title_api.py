# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from oxtornado import actions
from . import models
from . import query


import logging
logger = logging.getLogger('oml.item.title_api')


def editTitle(data):
    '''
        takes {
            id       string
            sortname string
        }
    '''
    response = {}
    '''
    item = models.Item.get(data['id'])
    item.sortname = unicodedata.normalize('NFKD', data['sortname'])
    item.save()
    response['name'] = item.name
    response['sortname'] = item.sortname
    '''
    return response
actions.register(editTitle)

def findTitles(data):
    '''
        takes {
            query {
                conditions [{}]
                operator   string
            }
            keys  [string]
            sort  [{}]
            range [int, int]
        }
    '''
    response = {}
    #q = query.parse(data)
    q = {
        'qs': models.Item.query,
    }
    if 'range' in data:
        q['range'] = data['range']

    if 'position' in data:
        pass
        #ids = [i.id for i in q['qs'].options(load_only('id'))]
        #response['position'] = utils.get_positions(ids, [data['qs'][0].id])[0]
        print('fixme', data)
    elif 'positions' in data:
        #ids = [i.id for i in q['qs'].options(load_only('id'))]
        #response['positions'] = utils.get_positions(ids, data['positions'])
        response['positions'] = []
        print('fixme', data)
    elif 'keys' in data:
        response['items'] = []
        for i in q['qs'][q['range'][0]:q['range'][1]]:
            j = {}
            for key in (data['keys'] or ['title', 'sorttitle']):
                if key == 'title':
                    j[key] = i.info.get(key)
                elif key == 'sorttitle':
                    j[key] = i.sort[0].title
            response['items'].append(j)
    else:
        response['items'] = q['qs'].count()
    return response
actions.register(findTitles)
