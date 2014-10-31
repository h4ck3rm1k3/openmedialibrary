'use strict';

oml.ui.listInnerPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SplitPanel({
            elements: [
                {
                    collapsed: !ui.showFilters,
                    collapsible: true,
                    element: oml.$ui.filtersOuterPanel = oml.ui.filtersOuterPanel(),
                    resizable: true,
                    resize: [96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 256],
                    size: ui.filtersSize,
                    tooltip: Ox._('filters') + ' <span class="OxBright">'
                        + Ox.SYMBOLS.shift + 'F</span>'
                },
                {
                    element: oml.$ui.list = oml.ui.list()
                },
                {
                    element: oml.$ui.statusbar = oml.ui.statusbar(),
                    size: 16
                }
            ],
            orientation: 'vertical'
        })
        .bindEvent({
            oml_listview: function() {
                that.replaceElement(1, oml.$ui.list = oml.ui.list());
            },
            oml_showfilters: function(data) {
                data.value == that.options('elements')[0].collapsed && that.toggleElement(0);
            }
        });

    return that;

};
