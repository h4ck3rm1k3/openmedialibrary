'use strict';

oml.ui.findForm = function(list) {

    var ui = oml.user.ui,

        that = Ox.Element(),

        $filter = Ox.Filter({
            findKeys: oml.config.itemKeys.map(function(key) {
                return Ox.extend({}, key, {
                    title: Ox._(key.title),
                    type: key.id == 'mediastate' ? 'item' : key.type,
                    format: key.format && key.format.type == 'upper' ? void 0 : key.format
                });
            }).concat([{
                id: 'list',
                title: Ox._('List'),
                type: 'item',
                values: ui._lists.filter(function(list) {
                    return Ox.contains(['library', 'static'], list.type);
                }).map(function(list) {
                    return {id: list.id, title: list.title};
                })
            }]),
            list: list ? null : {
                sort: ui.listSort,
                view: ui.listView
            },
            sortKeys: oml.config.sortKeys,
            value: Ox.clone(list ? list.query : ui.find, true),
            viewKeys: oml.config.listViews
        })
        .bindEvent({
            change: function(data) {
                (list ? oml.api.editList : Ox.noop)(list ? {
                    id: list.id,
                    query: data.value
                } : {}, function(result) {
                    if (list || ui.updateAdvancedFindResults) {
                        updateResults();
                    }
                });
            }
        })
        .appendTo(that);

    function updateResults() {
        if (list || ui.updateAdvancedFindResults) {
            Ox.Request.clearCache();
            oml.$ui.list.reloadList();
            oml.$ui.filters.forEach(function($filter) {
                $filter.reloadList();
            });
        } else {
            oml.UI.set({find: Ox.clone($filter.options('value'), true)});
            oml.$ui.findElement.updateElement();
        }
    }

    that.getList = $filter.getList;
    that.value = $filter.value;

    return that;

};
