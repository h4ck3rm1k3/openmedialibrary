'use strict';

oml.ui.updateButton = function() {

    var that = Ox.Element({
            tooltip: Ox._('Updates Available')
        })
        .css({
            marginRight: '3px'
        }).hide();

    function check() {
        oml.api.getVersion(function(response) {
            if (response.data.update) {
                that.show();
            } else {
                that.hide();
            }
        });
    }
    check();
    setTimeout(check, 86400000);

    Ox.Button({
            style: 'symbol',
            title: 'upload',
            type: 'image'
        })
        .css({
            float: 'left',
            borderRadius: 0
        })
        .bindEvent({
            click: function() {
                oml.UI.set({
                    'page': 'app',
                    'part.app': 'update'
                })
            }
        })
        .appendTo(that);

    return that;

};
