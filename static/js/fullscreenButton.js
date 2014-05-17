'use strict';

oml.ui.fullscreenButton = function() {

    var ui = oml.user.ui,

        that = Ox.Button({
            style: 'squared',
            title: 'grow',
            tooltip: Ox._('Enter Fullscreen'),
            type: 'image'
        })
        .css({
            float: 'left',
            margin: '4px 2px'
        })
        .bindEvent({
            click: function() {
                Ox.Fullscreen.enter(oml.$ui.viewer.find('iframe')[0]);
            },
            oml_itemview: function() {
                that.updateElement();
            }
        });

    that.updateElement = function() {
        return that.options({
            disabled: ui.itemView != 'book'
        });
    };

    return that.updateElement();

};