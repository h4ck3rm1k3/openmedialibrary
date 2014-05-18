'use strict';

oml.ui.appPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SplitPanel({
            elements: [
                {
                    element: oml.$ui.mainMenu = oml.ui.mainMenu(),
                    size: 20
                },
                {
                    element: oml.$ui.mainPanel = oml.ui.mainPanel()
                }
            ],
            orientation: 'vertical'
        })
        .bindEvent({
            oml_page: function(data) {
                setPage(data.value, data.previousValue);
            }
        });

    setPage(ui.page);

    function setPage(page, previousPage) {
        // close dialogs
        if (
            !Ox.contains(['import', 'export'], page)
            || !Ox.contains(['import', 'export'], previousPage)
        ) {
            $('.OxDialog:visible').each(function() {
                Ox.UI.elements[$(this).data('oxid')].close();
            });
        }
        // open dialog
        if (Ox.contains([
            'welcome', 'app', 'preferences', 'users',
            'notifications', 'transfers', 'help'
        ], page)) {
            oml.$ui[page + 'Dialog'] = oml.ui[page + 'Dialog']().open();
        } else if (Ox.contains(['import', 'export'], page)) {
            if (
                oml.$ui.importExportDialog
                && oml.$ui.importExportDialog.is(':visible')
            ) {
                oml.$ui.importExportDialog.select(page);
            } else {
                oml.$ui.importExportDialog = oml.ui.importExportDialog(page).open();
            }
        }
    }

    that.reload = function() {
        Ox.Request.cancel();
        Ox.Request.clearCache();
        oml.unbindEvent();
        oml.$ui.appPanel.remove();
        oml.$ui.appPanel = oml.ui.appPanel().appendTo(Ox.$body);
        return that;
    };

    return that;

};