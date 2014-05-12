# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from sqlalchemy.sql.expression import and_, not_, or_, ClauseElement
from datetime import datetime
import unicodedata
from sqlalchemy.sql import operators, extract

import utils
import settings

def get_operator(op, type='str'):
    return {
        'str': {
            '==': operators.ilike_op,
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

    def __init__(self, model):
        self._model = model
        self._find = model.find.mapper.class_
        self._user = model.users.mapper.class_
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
            if isinstance(v, unicode):
                v = unicodedata.normalize('NFKD', v).lower()
            q = get_operator(op)(self._find.value, v.lower())
            if k != '*':
                q &= (self._find.key == k)
            if exclude:
                q = ~q
            return q
        elif k == 'list':
            '''
            q = Q(id=0)
            l = v.split(":")
            if len(l) == 1:
                vqs = Volume.objects.filter(name=v, user=user)
                if vqs.count() == 1:
                    v = vqs[0]
                    q = Q(files__instances__volume__id=v.id)
            elif len(l) >= 2:
                l = (l[0], ":".join(l[1:]))
                lqs = list(List.objects.filter(name=l[1], user__username=l[0]))
                if len(lqs) == 1 and lqs[0].accessible(user):
                        l = lqs[0]
                        if l.query.get('static', False) == False:
                            data = l.query
                            q = self.parse_conditions(data.get('conditions', []),
                                                data.get('operator', '&'),
                                                user, l.user)
                        else:
                            q = Q(id__in=l.items.all())
                        if exclude:
                            q = ~q
                else:
                    q = Q(id=0)
            '''
            l = v.split(":")
            nickname = l[0]
            name = ':'.join(l[1:])
            if nickname:
                p = self._user.query.filter_by(nickname=nickname).first()
                v = '%s:%s' % (p.id, name)
            else:
                p = self._user.query.filter_by(id=settings.USER_ID).first()
                v = ':%s' % name
            #print 'get list:', p.id, name, l, v
            if name:
                l = self._list.query.filter_by(user_id=p.id, name=name).first()
            else:
                l = None
            if l:
                v = l.find_id
            if l and l._query:
                data = l._query
                q = self.parse_conditions(data.get('conditions', []),
                                    data.get('operator', '&'))
            else:
                q = (self._find.key == 'list') & (self._find.value == v)
            return q
        elif key_type == 'date':
            def parse_date(d):
                while len(d) < 3:
                    d.append(1)
                return datetime(*[int(i) for i in d])
            #using sort here since find only contains strings
            v = parse_date(v.split('-'))
            vk = getattr(self._model, 'sort_%s' % k)
            q = get_operator(op, 'int')(vk, v)
            if exclude:
                q = ~q
            return q
        else: #integer, float, time
            q = get_operator(op, 'int')(getattr(self._model, 'sort_%s'%k), v)
            if exclude:
                q = ~q
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
            qs = qs.join(self._find).filter(c)
        qs = qs.group_by(self._model.id)
        return qs

