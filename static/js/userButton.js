'use strict';

oml.ui.userButton = function() {

    var that = Ox.Element({
            tooltip: Ox._('Click to open preferences')
        })
        .css({
            marginRight: '3px'
        })
        .bindEvent({
            // ...
        });

    Ox.Button({
            style: 'symbol',
            title: 'user',
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
        .html('anonymous')
        .appendTo(that);

    return that;

};