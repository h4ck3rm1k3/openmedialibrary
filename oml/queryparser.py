# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from datetime import datetime
import unicodedata
from sqlalchemy.sql import operators
from sqlalchemy.orm import load_only

import utils
import settings

import logging
logger = logging.getLogger(__name__)

def get_operator(op, type='str'):
    return {
        'str': {
            '==': operators.eq,
            '>': operators.gt,
            '>=': operators.ge,
            '<': operators.lt,
            '<=': operators.le,
            '^': operators.startswith_op,
            '$': operators.endswith_op,
        },
        'int':  {
            '==': operators.eq,
            '>': operators.gt,
            '>=': operators.ge,
            '<': operators.lt,
            '<=': operators.le,
        }
    }[type].get(op, {
        'str': operators.contains_op,
        'int': operators.eq
    }[type])


class Parser(object):

    def __init__(self, model, user_items):
        self._model = model
        self._find = model.find.mapper.class_
        self._sort = model.sort.mapper.class_
        self._user = model.users.mapper.class_
        self._user_items = user_items
        self._list = model.lists.mapper.class_
        self.item_keys = model.item_keys
        self.filter_keys = model.filter_keys

    def parse_condition(self, condition):
        '''
        condition: {
                value: "war"
        }
        or
        condition: {
                key: "year",
                value: [1970, 1980],
                operator: "="
        }
        ...
        '''
        #logger.debug('parse_condition %s', condition)
        if not 'value' in condition:
            return None
        k = condition.get('key', '*')
        if not k:
            k = '*'
        v = condition['value']
        op = condition.get('operator')
        if not op:
            op = '='
        if op.startswith('!'):
            op = op[1:]
            exclude = True
        else:
            exclude = False

        key_type = (utils.get_by_id(self.item_keys, k) or {'type': 'string'}).get('type')
        if isinstance(key_type, list):
            key_type = key_type[0]
        if k == 'list':
            key_type = ''

        if (not exclude and op == '=' or op in ('$', '^')) and v == '':
            return None
        elif k == 'resolution':
            q = self.parse_condition({'key': 'width', 'value': v[0], 'operator': op}) \
                & self.parse_condition({'key': 'height', 'value': v[1], 'operator': op})
            if exclude:
                q = ~q
            return q
        elif isinstance(v, list) and len(v) == 2 and op == '=':
            q = self.parse_condition({'key': k, 'value': v[0], 'operator': '>='}) \
                & self.parse_condition({'key': k, 'value': v[1], 'operator': '<'})
            if exclude:
                q = ~q
            return q
        elif key_type == 'boolean':
            q = getattr(self._model, 'find_%s' % k) == v
            if exclude:
                q = ~q
            return q
        elif key_type in ("string", "text"):
            if isinstance(v, str):
                v = unicodedata.normalize('NFKD', v).lower()
            else:
                v = v.lower()
            q = get_operator(op)(self._find.findvalue, v)
            if k != '*':
                q &= (self._find.key == k)
            ids = self._model.query.join(self._find).filter(q).options(load_only('id'))
            in_op = operators.notin_op if exclude else operators.in_op
            q = in_op(self._model.id, ids)
            return q
        elif k == 'list':
            nickname, name = v.split(':', 1)
            if nickname:
                u = self._user.query.filter_by(nickname=nickname).one()
            else:
                u = self._user.query.filter_by(id=settings.USER_ID).one()
            l = self._list.query.filter_by(user_id=u.id, name=name).one()
            ids = l.get_items().options(load_only('id'))
            in_op = operators.notin_op if exclude else operators.in_op
            q = in_op(self._model.id, ids)
            return q
        elif key_type == 'date':
            def parse_date(d):
                while len(d) < 3:
                    d.append(1)
                return datetime(*[int(i) for i in d])
            #using sort here since find only contains strings
            v = parse_date(v.split('-'))
            vk = getattr(self._sort, k)
            q = get_operator(op, 'int')(vk, v)
            ids = self._model.query.join(self._find).filter(q).options(load_only('id'))
            in_op = operators.notin_op if exclude else operators.in_op
            q = in_op(self._model.id, ids)
            return q
        else: #integer, float, time
            q = get_operator(op, 'int')(getattr(self._sort, k), v)
            ids = self._model.query.join(self._find).filter(q).options(load_only('id'))
            in_op = operators.notin_op if exclude else operators.in_op
            q = in_op(self._model.id, ids)
            return q

    def parse_conditions(self, conditions, operator):
        '''
        conditions: [
            {
                value: "war"
            }
            {
                key: "year",
                value: "1970-1980,
                operator: "!="
            },
            {
                key: "country",
                value: "f",
                operator: "^"
            }
        ],
        operator: "&"
        '''
        conn = []
        for condition in conditions:
            if 'conditions' in condition:
                q = self.parse_conditions(condition['conditions'],
                                 condition.get('operator', '&'))
            else:
                q = self.parse_condition(condition)
            if isinstance(q, list):
                conn += q
            else:
                conn.append(q)
        conn = [q for q in conn if not isinstance(q, None.__class__)]
        if conn:
            if operator == '|':
                q = conn[0]
                for c in conn[1:]:
                    q = q | c
                q = [q]
            else:
                q = conn
            return q
        return []

    def find(self, data):
        '''
            query: {
                conditions: [
                    {
                        value: "war"
                    }
                    {
                        key: "year",
                        value: "1970-1980,
                        operator: "!="
                    },
                    {
                        key: "country",
                        value: "f",
                        operator: "^"
                    }
                ],
                operator: "&"
            }
        '''

        #join query with operator
        qs = self._model.query
        #only include items that have hard metadata
        conditions = self.parse_conditions(data.get('query', {}).get('conditions', []),
                                     data.get('query', {}).get('operator', '&'))
        for c in conditions:
            qs = qs.filter(c)
        #print(qs)
        return qs
