'use strict';

oml.ui.listViewButtons = function() {

    var ui = oml.user.ui,

        that = Ox.ButtonGroup({
            buttons: oml.config.listViews.map(function(view) {
                return Ox.extend({
                    tooltip: Ox._('View as') + ' ' + view.title
                }, view);
            }),
            selectable: true,
            style: 'squared',
            type: 'image',
            value: ui.listView
        }).css({
            float: 'left',
            margin: '4px 2px'
        })
        .bindEvent({
            change: function(data) {
                oml.UI.set({listView: data.value});
            },
            oml_listview: function() {
                that.updateElement();
            }
        });

    that.updateElement = function() {
        return that.options({value: ui.listView});
    };

    return that;

};