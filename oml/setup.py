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

def upgrade_db(old):
    if old <= '20140527-120-3cb9819':
        run_sql('CREATE INDEX ix_find_findvalue ON find (findvalue)')

def create_default_lists(user_id=None):
    with db.session():
        user_id = user_id or settings.USER_ID
        user = User.get_or_create(user_id)
        user.update_name()
        for list in settings.config['lists']:
            l = List.get(user_id, list['title'])
            if not l:
                l = List.create(user_id, list['title'], list.get('query'))

