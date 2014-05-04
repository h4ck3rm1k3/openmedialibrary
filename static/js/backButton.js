'use strict';

oml.ui.backButton = function() {

    var ui = oml.user.ui,

        that = Ox.Button({
            style: 'squared',
            title: 'arrowLeft',
            tooltip: Ox._('Back to Books'),
            type: 'image'
        })
        .css({
            float: 'left',
            margin: '4px 2px 4px 4px'
        })
        .bindEvent({
            click: function() {
                oml.UI.set({item: ''});
            }
        });

    return that;

};