'use strict';

oml.ui.mainPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SplitPanel({
            elements: [
                {
                    collapsible: true,
                    collapsed: !ui.showSidebar,
                    element: oml.$ui.leftPanel = oml.ui.leftPanel(),
                    resizable: true,
                    resize: [192, 256, 320, 384],
                    size: ui.sidebarSize,
                    tooltip: Ox._('sidebar') + ' <span class="OxBright">'
                        + Ox.SYMBOLS.shift + 'S</span>'
                },
                {
                    element: oml.$ui.rightPanel = oml.ui.rightPanel()
                }
            ],
            orientation: 'horizontal'
        })
        .bindEvent({
            oml_showsidebar: function(data) {
                data.value == that.options('elements')[0].collapsed && that.toggleElement(0);
            }
        });

    return that;

};
