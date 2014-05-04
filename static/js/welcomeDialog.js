'use strict';

oml.ui.welcomeDialog = function() {

    var that = oml.ui.iconDialog({
            buttons: [
                Ox.Button({
                    id: 'close',
                    title: Ox._('Close')
                })
                .bindEvent({
                    click: function() {
                        oml.UI.set({page: ''});
                    }
                })
            ],
            content: 'Welcome! To get started, you may want to set your '
                + 'library path, import some media, start your node, chose a '
                + 'username and add a few peers.',
            title: Ox._('Welcome to Open Media Library')
        });

    return that;

};