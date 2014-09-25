'use strict';

oml.ui.itemInnerPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SplitPanel({
            elements: [
                {
                    collapsed: !ui.showBrowser,
                    collapsible: true,
                    element: oml.$ui.browser = oml.ui.browser(),
                    size: 112 + Ox.UI.SCROLLBAR_SIZE,
                    tooltip: Ox._('browser')
                        + ' <span class="OxBright">'
                        + Ox.SYMBOLS.SHIFT + 'B</span>'
                },
                {
                    element: oml.$ui.itemViewPanel = oml.ui.itemViewPanel()
                }
            ],
            orientation: 'vertical'
        })
        .bindEvent({
            oml_showbrowser: function(data) {
                data.value == that.options('elements')[0].collapsed && that.toggleElement(0);
            }
        });

    return that;

};

