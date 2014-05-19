'use strict';

oml.ui.statusIcon = function(user, index) {

    // FIXME: not only '-webkit'

    var status = getStatus(user),
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
            borderRadius: '5px'
        })
        .append(
            $('<div>')
                .css({
                    width: '8px',
                    height: '8px',
                    margin: '1px',
                    borderRadius: '4px'
                })
        );

    render();

    if (user) {
        var superRemove = that.remove;
        that.remove = function() {
            oml.unbindEvent({
                status: update
            })
            superRemove();
        };
        oml.bindEvent({
            status: update
        });
    }

    function getStatus(data) {
        return !oml.user.online ? 'unknown'
        : data.online ? 'connected'
        : 'disconnected';
    }

    function render() {
        var color = {
                connected: [[64, 255, 64], [0, 192, 0]],
                disconnected: [[255, 64, 64], [192, 0, 0]],
                transferring: [[64, 255, 255], [0, 192, 192]],
                unknown: [[255, 255, 64], [192, 192, 0]]
            }[status].map(function(rgb) {
                return 'rgb(' + rgb.join(', ') + ')';
            }).join(', ');
        that.options({
            tooltip: Ox._({
                connected: 'Connected',
                disconnected: 'Disconnected',
                transferring: 'Transferring'
            }[status])
        }).css({
            background: '-webkit-linear-gradient(bottom, ' + color + ')',
        });
        that.find('div').css({
            background: '-webkit-linear-gradient(top, ' + color + ')',
        });
    }

    function update(data) {
        if (data.id == user.id) {
            var newStatus = getStatus(data);
            if (status != newStatus) {
                status = newStatus;
                render();
            }
        }
    }

    return that;

};
