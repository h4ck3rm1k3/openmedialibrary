'use strict';

oml.ui.rightPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SlidePanel({
            elements: [
                {
                    id: 'list',
                    element: oml.$ui.listOuterPanel = oml.ui.listOuterPanel()
                },
                {
                    id: 'item',
                    element: oml.$ui.itemOuterPanel = oml.ui.itemOuterPanel()
                }
            ],
            orientation: 'horizontal',
            selected: !ui.item ? 'list' : 'item',
            size: window.innerWidth - ui.showSidebar * ui.sidebarSize - 1
        })
        .bindEvent({
            resize: function(data) {
                that.options({size: data.size});
                oml.$ui.filtersOuterPanel.update();
                oml.$ui.itemViewPanel.options({size: data.size});
            },
            oml_item: function(data) {
                if (!!data.value != !!data.previousValue) {
                    that.options({selected: !ui.item ? 'list' : 'item'});
                }
            }
        });

    return that;

};