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
        }),
        bandwidth;

    /*
    oml.ui.statusIcon(oml.user)
        .css({float: 'left'})
        .appendTo(that);
    */

    function formatBandwidth(up, down) {
        return '&darr;'+Ox.formatValue(down, 'b')+' / &uarr;'+Ox.formatValue(up, 'b')+'';
    }

    bandwidth = Ox.Element()
        .addClass('OxLight')
        .css({
            float: 'left',
            marginTop: '2px',
            fontSize: '9px'
        })
        .html(formatBandwidth(0, 0))
        .appendTo(that);

    oml.bindEvent({
        bandwidth: function(data) {
            bandwidth.html(formatBandwidth(data.up, data.down));
        }
    });
    return that;

};
