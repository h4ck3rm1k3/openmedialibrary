'use strict';

oml.ui.itemViewPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SlidePanel({
            elements: [
                {
                    id: 'info',
                    element: oml.$ui.infoView = oml.ui.infoView()
                },
                {
                    id: 'book',
                    element: oml.$ui.viewer = oml.ui.viewer()
                }
            ],
            orientation: 'horizontal',
            selected: ui.itemView,
            size: window.innerWidth - ui.sidebarSize - 1
        })
        .bindEvent({
            oml_itemview: function(data) {
                that.options({selected: data.value});
            }
        });

    return that;

};