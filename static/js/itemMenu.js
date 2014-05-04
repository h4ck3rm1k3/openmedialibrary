'use strict';

oml.ui.itemMenu = function() {

    var ui = oml.user.ui,

        that = Ox.Button({
            style: 'squared',
            title: 'set',
            tooltip: Ox._('Options'),
            type: 'image'
        })
        .css({
            float: 'left',
            margin: '4px 2px'
        });

    return that;

};