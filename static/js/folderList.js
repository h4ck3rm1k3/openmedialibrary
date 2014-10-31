'use strict';

oml.ui.folderList = function(options) {

    var ui = oml.user.ui,

        that = Ox.TableList({
            columns: [
                {
                    format: function(value) {
                        return $('<img>')
                            .attr({
                                src: Ox.UI.getImageURL(
                                    value == 'libraries' ? 'symbolData'
                                        : value == 'library' ? 'symbolUser'
                                        : value == 'static' ? 'symbolClick'
                                        : 'symbolFind'
                                )
                            })
                            .css({
                                width: '10px',
                                height: '10px',
                                margin: '2px -2px 2px 0'
                            });
                    },
                    id: 'type',
                    visible: true,
                    width: 16
                },
                {
                    id: 'name',
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
                    visible: true,
                    width: 42
                }
            ],
            draggable: options.draggable,
            items: Ox.clone(options.items, true),
            sort: [{key: 'index', operator: '+'}],
            sortable: options.sortable,
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
