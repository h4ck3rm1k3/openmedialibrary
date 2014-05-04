'use strict';

oml.ui.errorDialog = function() {

    var ui = oml.user.ui,

        that = oml.ui.iconDialog({
                buttons: getButtons(),
                content: Ox.Element(),
                keys: {enter: 'close', escape: 'close'}
            })
            .addClass('OxErrorDialog')
            .bindEvent({
                oml_enabledebugmenu: function() {
                    that.options({buttons: getButtons()});
                }
            }),

        open = that.open;

    function getButtons() {
        return (ui.enableDebugMenu ? [
            Ox.Button({
                    title: Ox._('View Error Logs...')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                        oml.UI.set({page: 'errorlogs'});
                    }
                }),
            {}
        ] : []).concat([
            Ox.Button({
                    id: 'close',
                    title: Ox._('Close')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                    }
                })
        ]);
    }

    that.open = function() {
        // on window unload, pending request will time out, so
        // in order to keep the dialog from appearing, delay it
        setTimeout(function() {
            if ($('.OxErrorDialog').length == 0 && !oml.isUnloading) {
                open();
            }
        }, 250);
        return that;
    };

    that.update = function(data) {
        // 0 (timeout) or 500 (error)
        var error = data.status.code == 0 ? 'a timeout' : 'an error',
            title = data.status.code == 0 ? 'Timeout' : 'Error';
        that.options({
            content: Ox.Element().html(
                Ox._(
                    'Sorry, {0} occured while handling your request.'
                    + ' In case this happens repeatedly, you may want to file a bug report.'
                    + ' Otherwise, please try again later.', [error]
                )
            ),
            title: title
        });
        return that;
    }

    return that;

};
