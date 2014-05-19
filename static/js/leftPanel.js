'use strict';

oml.ui.leftPanel = function() {

    var ui = oml.user.ui,

        that = Ox.SplitPanel({
            elements: [
                {
                    element: oml.$ui.sectionbar = oml.ui.sectionbar(),
                    size: 24
                },
                {
                    element: oml.$ui.folders = oml.ui.folders()
                },
                {
                    collapsed: !oml.user.ui.showInfo,
                    collapsible: true,
                    element: oml.$ui.info = oml.ui.info(),
                    size: oml.getInfoHeight(),
                    tooltip: Ox._('info') + ' <span class="OxBright">'
                        + Ox.SYMBOLS.SHIFT + 'I</span>'
                }
            ],
            id: 'leftPanel',
            orientation: 'vertical'
        })
        .bindEvent({
            resize: function(data) {
                ui.sidebarSize = data.size;
                oml.resizeListFolders();
                that.size(2, oml.getInfoHeight());
                if (!ui.showInfo) {
                    that.css({bottom: -data.size + 'px'});
                }
            },
            resizeend: function(data) {
                // set to 0 so that UI.set registers a change of the value
                ui.sidebarSize = 0;
                oml.UI.set({sidebarSize: data.size});
            },
            toggle: function(data) {
                oml.UI.set({showSidebar: !data.collapsed});
                if (data.collapsed) {
                    oml.$ui.folderList.forEach(function($list) {
                        $list.loseFocus();
                    });
                }
            },
            oml_showinfo: function(data) {
                if (data.value == that.options('elements')[2].collapsed) {
                    that.toggle(2);
                }
            }
        });

    return that;

};