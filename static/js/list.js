'use strict';

oml.ui.list = function() {

    var ui = oml.user.ui,

        that = oml.ui[ui.listView + 'View']()
            .bindEvent({
                closepreview: function() {
                    oml.$ui.previewButton.options({value: false});
                    oml.$ui.previewDialog.close();
                    delete oml.$ui.previewDialog;
                },
                init: function(data) {
                    oml.$ui.statusbar.set('total', data);
                },
                open: function(data) {
                    oml.UI.set({
                        item: data.ids[0],
                        itemView: 'info'
                    });
                },
                openpreview: function() {
                    if (!oml.$ui.previewDialog) {
                        oml.$ui.previewButton.options({value: true});
                        oml.$ui.previewDialog = oml.ui.previewDialog()
                            .open()
                            .bindEvent({
                                close: function() {
                                    that.closePreview();
                                    delete oml.$ui.previewDialog;
                                }
                            });
                    } else {
                        oml.$ui.previewDialog.update();
                    }
                },
                resize: function(data) {
                    // this is the resize event of the split panel
                    that.size();
                },
                select: function(data) {
                    oml.UI.set({listSelection: data.ids});
                },
                oml_find: function() {
                    that.reloadList();
                },
                oml_item: function() {
                    if (!ui.item) {
                        that.gainFocus();
                    } else {
                        that.options({selected: [ui.item]});
                    }
                },
                oml_listselection: function(data) {
                    that.options({selected: data.value});
                },
                oml_listsort: function(data) {
                    that.options({sort: data.value});
                },
                oml_sidebarsize: function(data) {
                    that.size();
                }
            });

    oml.enableDragAndDrop(that);

    return that;

};