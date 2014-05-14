'use strict';

oml.ui.resetUIDialog = function(data) {

    var that = oml.ui.confirmDialog({
        buttons: [
            Ox.Button({
                title: Ox._('No, Don\'t Reset')
            }),
            Ox.Button({
                title: Ox._('Yes, Reset')
            })
        ],
        content: Ox._('Are you sure you want to reset all UI settings?'),
        title: Ox._('Reset UI Settings')
    }, function() {
        oml.$ui.preferencesDialog.close();
        oml.UI.set({page: ''});
        oml.UI.reset();
    });

    return that;

};
