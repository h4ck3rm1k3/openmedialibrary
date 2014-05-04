'use strict';

oml.ui.itemOuterPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SplitPanel({
            elements: [
                {
                    element: oml.$ui.itemToolbar = oml.ui.itemToolbar(),
                    size: 24
                },
                {
                    element: oml.$ui.itemInnerPanel = oml.ui.itemInnerPanel()
                }
            ],
            orientation: 'vertical'
        })
        .bindEvent({
            // ...
        });

    return that;

};