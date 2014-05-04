'use strict';

oml.ui.confirmDialog = function(options, callback) {

    options = Ox.extend(options, {
        buttons: options.buttons.map(function($button, index) {
            return $button
                .options({id: index ? 'yes' : 'no'})
                .bindEvent({
                    click: function() {
                        that.close();
                        index && callback();
                    }
                });
        }),
        keys: {enter: 'yes', escape: 'no'}
    });

    var that = oml.ui.iconDialog(options);

    return that.open();

}