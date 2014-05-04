'use strict';

oml.ui.listOuterPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SplitPanel({
            elements: [
                {
                    element: oml.$ui.listToolbar = oml.ui.listToolbar(),
                    size: 24
                },
                {
                    element: oml.$ui.listInnerPanel = oml.ui.listInnerPanel()
                }
            ],
            orientation: 'vertical'
        })
        .bindEvent({
            // ...
        });

    return that;

};