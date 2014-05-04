'use strict';

oml.ui.allItems = function(user) {

    var ui = oml.user.ui,

        that = Ox.TableList({
            columns: [
                {
                    format: function() {
                        return $('<img>')
                            .attr({
                                src: Ox.UI.getImageURL(user ? 'symbolUser' : 'symbolData')
                            })
                            .css({
                                width: '10px',
                                height: '10px',
                                margin: '2px -2px 2px 0'
                            });
                    },
                    id: 'id',
                    title: 'ID',
                    visible: true,
                    width: 16
                },
                {
                    id: 'title',
                    title: 'Title',
                    visible: true,
                    width: ui.sidebarSize - 58,
                },
                {
                    align: 'right',
                    format: function(value) {
                        return value > -1
                            ? '<span class="OxLight">'
                                + Ox.formatNumber(value)
                                + '</span>'
                            : '';
                    },
                    id: 'items',
                    title: 'Items',
                    visible: true,
                    width: 42
                }
            ],
            items: [
                {
                    id: '',
                    title: Ox._(user ? 'Library' : 'All Libraries'),
                    items: -1
                }
            ],
            sort: [{key: 'id', operator: '+'}],
            selected: [],
            unique: 'id'
        })
        .css({
            width: ui.sidebarSize + 'px',
            height: '16px'
        });

    that.resizeElement = function() {
        // ...
    };

    return that;

};