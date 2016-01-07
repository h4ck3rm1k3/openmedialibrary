# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

import settings
import db

from user.models import List, User

def run_sql(sql):
    with db.session() as session:
        session.connection().execute(sql)
        session.commit()

def create_db():
    if not os.path.exists(settings.db_path):
        sql = '''
CREATE TABLE item (
    created DATETIME, 
    modified DATETIME, 
    id VARCHAR(32) NOT NULL, 
    info BLOB, 
    meta BLOB, 
    added DATETIME, 
    accessed DATETIME, 
    timesaccessed INTEGER, 
    PRIMARY KEY (id)
);
CREATE TABLE changelog (
    id INTEGER NOT NULL, 
    created DATETIME, 
    timestamp BIGINT, 
    user_id VARCHAR(43), 
    revision BIGINT, 
    data TEXT, 
    sig VARCHAR(96), 
    PRIMARY KEY (id)
);
CREATE TABLE user (
    created DATETIME, 
    modified DATETIME, 
    id VARCHAR(43) NOT NULL, 
    info BLOB, 
    nickname VARCHAR(256), 
    pending VARCHAR(64), 
    queued BOOLEAN, 
    peered BOOLEAN, 
    online BOOLEAN, 
    PRIMARY KEY (id), 
    UNIQUE (nickname), 
    CHECK (queued IN (0, 1)), 
    CHECK (peered IN (0, 1)), 
    CHECK (online IN (0, 1))
);
CREATE TABLE metadata (
    created DATETIME, 
    modified DATETIME, 
    id INTEGER NOT NULL, 
    "key" VARCHAR(256), 
    value VARCHAR(256), 
    data BLOB, 
    PRIMARY KEY (id)
);
CREATE TABLE person (
    name VARCHAR(1024) NOT NULL, 
    sortname VARCHAR, 
    numberofnames INTEGER, 
    PRIMARY KEY (name)
);
CREATE TABLE transfer (
    item_id VARCHAR(32) NOT NULL, 
    added DATETIME, 
    progress FLOAT, 
    PRIMARY KEY (item_id), 
    FOREIGN KEY(item_id) REFERENCES item (id)
);
CREATE TABLE find (
    id INTEGER NOT NULL, 
    item_id VARCHAR(32), 
    "key" VARCHAR(200), 
    value TEXT, 
    findvalue TEXT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(item_id) REFERENCES item (id)
);
CREATE INDEX ix_find_key ON find ("key");
CREATE TABLE list (
    id INTEGER NOT NULL, 
    name VARCHAR, 
    index_ INTEGER, 
    type VARCHAR(64), 
    "query" BLOB, 
    user_id VARCHAR(43), 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE useritem (
    user_id VARCHAR(43), 
    item_id VARCHAR(32), 
    FOREIGN KEY(item_id) REFERENCES item (id), 
    FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE TABLE sort (
    item_id VARCHAR(32) NOT NULL, 
    title VARCHAR(1000), 
    author VARCHAR(1000), 
    publisher VARCHAR(1000), 
    place VARCHAR(1000), 
    country VARCHAR(1000), 
    date VARCHAR(1000), 
    language VARCHAR(1000), 
    pages BIGINT, 
    classification VARCHAR(1000), 
    extension VARCHAR(1000), 
    size BIGINT, 
    created DATETIME, 
    added DATETIME, 
    modified DATETIME, 
    accessed DATETIME, 
    timesaccessed BIGINT, 
    mediastate VARCHAR(1000), 
    transferadded DATETIME, 
    transferprogress FLOAT, 
    id VARCHAR(1000), 
    isbn VARCHAR(1000), 
    asin VARCHAR(1000), 
    lccn VARCHAR(1000), 
    olid VARCHAR(1000), 
    oclc VARCHAR(1000), 
    random BIGINT, 
    PRIMARY KEY (item_id), 
    FOREIGN KEY(item_id) REFERENCES item (id)
);
CREATE INDEX ix_sort_accessed ON sort (accessed);
CREATE INDEX ix_sort_added ON sort (added);
CREATE INDEX ix_sort_asin ON sort (asin);
CREATE INDEX ix_sort_author ON sort (author);
CREATE INDEX ix_sort_classification ON sort (classification);
CREATE INDEX ix_sort_country ON sort (country);
CREATE INDEX ix_sort_created ON sort (created);
CREATE INDEX ix_sort_date ON sort (date);
CREATE INDEX ix_sort_extension ON sort (extension);
CREATE INDEX ix_sort_id ON sort (id);
CREATE INDEX ix_sort_isbn ON sort (isbn);
CREATE INDEX ix_sort_language ON sort (language);
CREATE INDEX ix_sort_lccn ON sort (lccn);
CREATE INDEX ix_sort_mediastate ON sort (mediastate);
CREATE INDEX ix_sort_modified ON sort (modified);
CREATE INDEX ix_sort_oclc ON sort (oclc);
CREATE INDEX ix_sort_olid ON sort (olid);
CREATE INDEX ix_sort_pages ON sort (pages);
CREATE INDEX ix_sort_place ON sort (place);
CREATE INDEX ix_sort_publisher ON sort (publisher);
CREATE INDEX ix_sort_random ON sort (random);
CREATE INDEX ix_sort_size ON sort (size);
CREATE INDEX ix_sort_timesaccessed ON sort (timesaccessed);
CREATE INDEX ix_sort_title ON sort (title);
CREATE INDEX ix_sort_transferadded ON sort (transferadded);
CREATE INDEX ix_sort_transferprogress ON sort (transferprogress);
CREATE TABLE file (
    created DATETIME, 
    modified DATETIME, 
    sha1 VARCHAR(32) NOT NULL, 
    path VARCHAR(2048), 
    info BLOB, 
    item_id VARCHAR(32), 
    PRIMARY KEY (sha1), 
    FOREIGN KEY(item_id) REFERENCES item (id)
);
CREATE TABLE listitem (
    list_id INTEGER, 
    item_id VARCHAR(32), 
    FOREIGN KEY(item_id) REFERENCES item (id), 
    FOREIGN KEY(list_id) REFERENCES list (id)
);
PRAGMA journal_mode=WAL
'''
        for statement in sql.split(';'):
            run_sql(statement)
        upgrade_db('0')
        create_default_lists()

def upgrade_db(old, new=None):
    if new:
        if old <= '20140525-92-eac91e7' and new > '20140525-92-eac91e7':
            with db.session():
                import user.models
                for u in user.models.User.query:
                    u.update_name()
                    u.save()
                import item.models
                for f in item.models.File.query:
                    changed = False
                    for key in ('mediastate', 'coverRatio', 'previewRatio'):
                        if key in f.info:
                            del f.info[key]
                            changed = True
                    if changed:
                        f.save()
        if old <= '20140526-118-d451eb3' and new > '20140526-118-d451eb3':
            with db.session():
                import item.models
                item.models.Find.query.filter_by(key='list').delete()

    if old <= '20140527-120-3cb9819':
        run_sql('CREATE INDEX ix_find_findvalue ON find (findvalue)')

    if old <= '20150307-272-557f4d3':
        run_sql('''CREATE TABLE scrape (
    item_id VARCHAR(32) NOT NULL, 
    added DATETIME, 
    PRIMARY KEY (item_id), 
    FOREIGN KEY(item_id) REFERENCES item (id)
)''')
        run_sql('CREATE INDEX idx_scrape_added ON scrape (added)')
    if old <= '20151118-346-7e86e68':
        old_key = os.path.join(settings.config_path, 'node.ssl.key')
        if os.path.exists(old_key):
            os.unlink(old_key)
        statements = [
            "UPDATE user SET id = '{nid}' WHERE id = '{oid}'",
            "UPDATE list SET user_id = '{nid}' WHERE user_id = '{oid}'",
            "UPDATE useritem SET user_id = '{nid}' WHERE user_id = '{oid}'",
            "UPDATE changelog SET user_id = '{nid}' WHERE user_id = '{oid}'",
        ]
        for sql in statements:
            run_sql(sql.format(oid=settings.OLD_USER_ID, nid=settings.USER_ID))
    if old <= '20151201-384-03c2439':
        with db.session():
            import item.models
            for i in item.models.Item.query:
                for f in i.files.all():
                    f.move()
    if old <= '20160103-423-05ca6c9':
        with db.session():
            import item.models
            for i in item.models.Item.query:
                if 'id' in i.meta:
                    del i.meta['id']
                    i.save()
            for m in item.models.Metadata.query:
                if 'id' in m.data:
                    del m.data['id']
                    m.save()
    if old <= '20160106-495-d1b9e96':
        run_sql('CREATE INDEX ix_useritem_user ON useritem ("user_id")')
    if old <= '20160106-497-c86ba8a':
        with db.session() as session:
            u = User.get(settings.USER_ID)
            l = u.library
            for i in u.items.all():
                if not i in l.items:
                    l.items.append(i)
            session.add(l)
            u.clear_list_cache()
            for u in User.query.filter_by(peered=True):
                l = u.library
                for i in u.items.all():
                    if not i in l.items:
                        l.items.append(i)
                session.add(l)
                u.clear_list_cache()
                l.items_count()
            session.commit()
    if old <= '20160106-500-4c87307':
        with db.session() as session:
            l = user.models.List.query.filter_by(name=' [2]', user_id=settings.USER_ID).first()
            if l and not len(l.items):
                l.delete()

def create_default_lists(user_id=None):
    with db.session():
        user_id = user_id or settings.USER_ID
        user = User.get_or_create(user_id)
        user.update_name()
        for list in settings.config['lists']:
            l = List.get(user_id, list['title'])
            if not l:
                l = List.create(user_id, list['title'], list.get('query'))

