# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import os


def cover(path):
    data = None
    #open rar file and extract first page here
    return data

def info(path):
    data = {}
    data['title'] = os.path.splitext(os.path.basename(path))[0]
    #data['pages'] = fixme read rar to count pages
    return data

