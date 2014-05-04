'use strict';

oml.ui.listView = function() {

    var ui = oml.user.ui,

        that = Ox.TableList({
            columns: oml.config.sortKeys.map(function(key) {
                var position = ui.listColumns.indexOf(key.id);
                return {
                    addable: key.id != 'random',
                    align: ['string', 'text'].indexOf(
                        Ox.isArray(key.type) ? key.type[0]: key.type
                    ) > -1 ? 'left' : key.type == 'list' ? 'center' : 'right',
                    defaultWidth: key.columnWidth,
                    format: key.format,
                    id: key.id,
                    operator: key.operator,
                    position: position,
                    removable: !key.columnRequired,
                    title: Ox._(key.title),
                    type: key.type,
                    visible: position > -1,
                    width: ui.listColumnWidth[key.id] || key.columnWidth
                };
            }),
            columnsMovable: true,
            columnsRemovable: true,
            columnsResizable: true,
            columnsVisible: true,
            items: function(data, callback) {
                oml.api.find(Ox.extend(data, {
                    query: ui.find
                }), callback);
            },
            draggable: true,
            scrollbarVisible: true,
            selected: ui.listSelection,
            sort: ui.listSort,
            unique: 'id'
        })
        .bindEvent({
            columnchange: function(data) {
                oml.UI.set({listColumns: data.ids});
            },
            columnresize: function(data) {
                oml.UI.set('listColumnWidth.' + data.id, data.width);
            },
            sort: function(data) {
                oml.UI.set({
                    listSort: [{key: data.key, operator: data.operator}]
                });
            }
        });

    return that;

};