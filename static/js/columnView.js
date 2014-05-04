'use strict';

oml.ui.columnView = function() {

    var ui = oml.user.ui,

        that = Ox.CustomColumnList({
            columns: [
                {
                    id: 'authors',
                    item: getItemFunction('authors'),
                    itemHeight: 32,
                    items: function(data, selected, callback) {
                        oml.api.find(Ox.extend({
                            group: 'author',
                            query: {conditions: [], operator: '&'}
                        }, data), callback);
                    },
                    keys: ['name', 'items'],
                    max: -1,
                    sort: [{key: 'name', operator: '+'}],
                    selected: [],
                    title: Ox._('Authors'),
                    unique: 'name'
                },
                {
                    id: 'items',
                    item: getItemFunction('items'),
                    itemHeight: 32,
                    items: function(data, selected, callback) {
                        if (selected[0].length) {
                            oml.api.find(Ox.extend({
                                query: {
                                    conditions: selected[0].map(function(name) {
                                        return {
                                            key: 'author',
                                            operator: '==',
                                            value: name
                                        };
                                    }),
                                    operator: '|'
                                }
                            }, data), callback);
                        } else {
                            callback({
                                data: {
                                    items: data.keys ? [] : 0
                                }
                            });
                        }
                    },
                    keys: ['author', 'title', 'date'],
                    max: -1,
                    selected: [],
                    sort: [{key: 'title', operator: '+'}],
                    title: Ox._('Items'),
                    unique: 'id'
                },
                {
                    id: 'files',
                    item: getItemFunction('files'),
                    itemHeight: 32,
                    items: function(data, selected, callback) {
                        oml.api.find(Ox.extend({
                            query: {
                                conditions: selected[0].map(function(name) {
                                    return {
                                        key: 'author',
                                        operator: '==',
                                        value: name
                                    };
                                }),
                                operator: '|'
                            }
                        }, data), callback);
                    },
                    keys: ['id', 'name'],
                    selected: [],
                    sort: [{key: 'name', operator: '+'}],
                    title: Ox._('Files'),
                    unique: 'id'
                }
            ],
            width: window.innerWidth - (ui.showSidebar * ui.sidebarSize) - 1
        });

    function getItemFunction(id) {
        return function(data, width) {
            var $item = $('<div>')
                .css({
                    height: '32px',
                    width: width + 'px'
                })
            if (!Ox.isEmpty(data)) {
                $('<img>')
                    .attr({
                        src: '/static/png/oml.png'
                    })
                    .css({
                        position: 'relative',
                        display: 'inline-block',
                        left: '2px',
                        top: '2px',
                        width: '26px',
                        height: '26px',
                        border: '1px solid rgb(192, 192, 192)',
                        backgroundImage: '-webkit-linear-gradient(top, rgb(255, 255, 255), rgb(224, 224, 224))'
                    })
                    .appendTo($item);
                $('<div>')
                    .css({
                        position: 'relative',
                        left: '34px',
                        top: '-28px',
                        width: width - 36 + 'px',
                        height: '16px',
                        fontSize: '13px',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        cursor: 'default'
                    })
                    .html(id == 'authors' ? data.name : 'foo')
                    .appendTo($item);
                $('<div>')
                    .addClass('OxLight')
                    .css({
                        position: 'relative',
                        left: '34px',
                        top: '-28px',
                        width: width - 36 + 'px',
                        height: '12px',
                        fontSize: '9px',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        cursor: 'default'
                    })
                    .html(id == 'authors' ? Ox.formatCount(data.items, 'Item') : 'bar')
                    .appendTo($item);
            }
            return $item;
        };
    }

    return that;

};