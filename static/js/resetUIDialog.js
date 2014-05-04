'use strict';

oml.ui.resetUIDialog = function(data) {

    var that = oml.ui.iconDialog({
        buttons: [
            Ox.Button({
                    id: 'cancel',
                    title: Ox._('Don\'t Reset')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                    }
                }),
            Ox.Button({
                    id: 'reset',
                    title: Ox._('Reset')
                }).bindEvent({
                    click: function() {
                        that.close();
                        oml.$ui.preferencesDialog.close();
                        oml.UI.set({page: ''});
                        oml.UI.reset();
                    }
                })
        ],
        content: Ox._('Are you sure you want to reset all UI settings?'),
        keys: {enter: 'reset', escape: 'cancel'},
        title: Ox._('Reset UI Settings')
    });

    return that;

};
