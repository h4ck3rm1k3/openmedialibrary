'use strict';

oml.ui.findForm = function(list) {

    //Ox.print('FIND FORM LIST QUERY', list.query);

    var ui = oml.user.ui,

        that = Ox.Element(),

        $filter = Ox.Filter({
            findKeys: oml.config.itemKeys.map(function(key) {
                return Ox.extend({}, key, {
                    title: Ox._(key.title),
                    type: key.id == 'mediastate' ? 'item' : key.type
                });
            }).concat([{
                id: 'list',
                title: Ox._('List'),
                type: 'item',
                values: ui._lists.filter(function(list) {
                    return list.type != 'smart'
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
                    if (ui.updateAdvancedFindResults) {
                        updateResults();
                    }
                });
            }
        })
        .appendTo(that);

    function updateResults() {
        if (list) {
            Ox.Request.clearCache(list.id);
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