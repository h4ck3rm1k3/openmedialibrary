'use strict';

oml.ui.statusIcon = function(status) {

    // FIXME: not only '-webkit'

    var color = {
            connected: [[64, 255, 64], [0, 192, 0]],
            disconnected: [[255, 64, 64], [192, 0, 0]],
            transferring: [[64, 255, 255], [0, 192, 192]],
            unknown: [[255, 255, 64], [192, 192, 0]]
        }[status].map(function(rgb) {
            return 'rgb(' + rgb.join(', ') + ')';
        }).join(', '),
    
        that = Ox.Element({
            tooltip: Ox._({
                connected: 'Connected',
                disconnected: 'Disconnected',
                transferring: 'Transferring'
            }[status])
        })
        .css({
            width: '10px',
            height: '10px',
            margin: '3px',
            background: '-webkit-linear-gradient(bottom, ' + color + ')',
            borderRadius: '5px'
        })
        .append(
            $('<div>')
                .css({
                    width: '8px',
                    height: '8px',
                    margin: '1px',
                    background: '-webkit-linear-gradient(top, ' + color + ')',
                    borderRadius: '4px'
                })
        );

    return that;

};