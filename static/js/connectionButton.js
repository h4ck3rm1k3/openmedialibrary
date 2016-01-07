'use strict';

oml.ui.connectionButton = function() {

    var that = Ox.Element({
            tooltip: Ox._('Transfers')
        })
        .css({
            marginRight: '3px'
        })
        .bindEvent({
            click: function() {
                oml.UI.set({page: 'transfers'});
            }
        }),

        bandwidth = Ox.Element()
            .addClass('OxLight')
            .css({
                float: 'left',
                marginTop: '2px',
                fontSize: '9px'
            })
            .html(formatBandwidth(0, 0))
            .appendTo(that);

    function formatBandwidth(up, down) {
        return '&darr; ' + Ox.formatValue(down, 'B')
            + ' / &uarr; ' + Ox.formatValue(up, 'B');
    }

    oml.bindEvent({
        bandwidth: function(data) {
            bandwidth.html(formatBandwidth(data.up, data.down));
        }
    });

    return that;

};
