'use strict';

oml.ui.itemViewButtons = function() {

    var ui = oml.user.ui,

        that = Ox.ButtonGroup({
            buttons: [
                {
                    id: 'info',
                    title: 'iconlist',
                    tooltip: Ox._('View Info')
                },
                {
                    id: 'book',
                    title: 'book',
                    tooltip: Ox._('Read Book')
                }
            ],
            selectable: true,
            style: 'squared',
            type: 'image'
        }).css({
            float: 'left',
            margin: '4px 2px'
        })
        .bindEvent({
            change: function(data) {
                oml.UI.set({itemView: data.value});
            },
            oml_item: function() {
                if (ui.item) {
                    that.update();
                } else {
                    that.disableButton('book');
                }
            },
            oml_itemview: function(data) {
                that.update();
            }
        });

    that.update = function() {
        var item = ui.item;
        that.options({
            disabled: ui.itemView != 'book',
            value: ui.itemView
        });
        oml.api.get({
            id: item,
            keys: ['mediastate']
        }, function(result) {
            if (item == ui.item) {
                that[
                    result.data.mediastate == 'available'
                    ? 'enableButton' : 'disableButton'
                ]('book');
            }
        });
        return that;
    };

    oml.bindEvent({
        transfer: function(data) {
            if (data.id == ui.item && data.progress == 1) {
                that.enableButton('book');
            }
        }
    });

    return that.update();

};