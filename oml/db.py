from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData
from sqlalchemy import orm
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.ext.declarative import declarative_base


import settings
import state

engine = create_engine('sqlite:////%s' % settings.db_path)
Session = scoped_session(sessionmaker(bind=engine))

metadata = MetaData()


class _QueryProperty(object):

    def __init__(self):
        pass

    def __get__(self, obj, type):
        try:
            mapper = orm.class_mapper(type)
            if mapper:
                return type.query_class(mapper, session=state.db.session)
        except UnmappedClassError:
            return None

class BaseQuery(orm.Query):
    pass

Model = declarative_base()
Model.query_class = BaseQuery
Model.query = _QueryProperty()
Model.metadata = metadata

@contextmanager
def session():
    if hasattr(state.db, 'session'):
        state.db.count += 1
    else:
        state.db.session = Session()
        state.db.count = 1
    try:
        yield state.db.session
    finally:
        state.db.count -= 1
        if not state.db.count:
            state.db.session.close()
            Session.remove()

class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()
