'use strict';

oml.ui.connectionButton = function() {

    var that = Ox.Element({
            tooltip: Ox._('Disconnected')
        })
        .css({
            marginRight: '3px'
        })
        .bindEvent({
            // ...
        });

    /*
    oml.ui.statusIcon(oml.user.online ? 'connected' : 'disconnected')
        .css({float: 'left'})
        .appendTo(that);
    */

    Ox.Element()
        .addClass('OxLight')
        .css({
            float: 'left',
            marginTop: '2px',
            fontSize: '9px'
        })
        .html('&darr;0K/&uarr;0K')
        .appendTo(that);

    return that;

};