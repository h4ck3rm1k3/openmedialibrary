'use strict';

oml.ui.notificationsButton = function() {

    var that = Ox.Element({
            tooltip: Ox._('No notifications')
        })
        .css({
            marginRight: '3px'
        })
        .bindEvent({
            click: function() {
                // ...
            }
        });

    Ox.Button({
            style: 'symbol',
            title: 'playlist',
            type: 'image'
        })
        .css({
            float: 'left',
            borderRadius: 0
        })
        .appendTo(that);

    Ox.Element()
        .addClass('OxLight')
        .css({
            float: 'left',
            marginTop: '2px',
            fontSize: '9px'
        })
        .html('0')
        .appendTo(that);

    return that;

};