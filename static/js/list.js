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
                copy: function(data) {
                    oml.clipboard.copy(data.ids, 'item');
                },
                copyadd: function(data) {
                    oml.clipboard.copy(data.ids, 'item');
                },
                cut: function(data) {
                    var listData = oml.getListData();
                    if (listData.editable && listData.type == 'static') {
                        oml.clipboard.copy(data.ids, 'item');
                        oml.doHistory('cut', data.ids, ui._list, function() {
                            oml.UI.set({listSelection: []});
                            oml.$ui.folders.updateElement();
                            oml.$ui.list.updateElement();
                        });
                    }
                },
                cutadd: function(data) {
                    var listData = oml.getListData();
                    if (listData.editable && listData.type == 'static') {
                        oml.clipboard.add(data.ids, 'item');
                        oml.doHistory('cut', data.ids, ui._list, function() {
                            oml.UI.set({listSelection: []});
                            oml.$ui.folders.updateElement();
                            oml.$ui.list.updateElement();
                        });
                    }
                },
                'delete': function(data) {
                    var listData = oml.getListData();
                    if (listData.editable && listData.type == 'static') {
                        oml.doHistory('delete', data.ids, ui._list, function() {
                            oml.UI.set({listSelection: []});
                            oml.$ui.folders.updateItems();
                            oml.$ui.list.updateElement();
                        });
                    }
                },
                init: function(data) {
                    Ox.print('MAIN LIST INIT', data);
                    if (ui.find.conditions.length == 0 || (
                        ui.find.conditions.length == 1
                        && ui.find.conditions[0].key == 'list'
                        && ui.find.conditions[0].operator == '=='
                    )) {
                        oml.$ui.folders.updateItems(data.items);
                    }
                    oml.$ui.statusbar.set('total', data);
                },
                key_control_delete: function() {
                    var listData = oml.getListData();
                    if (listData.own) {
                        oml.ui.deleteItemsDialog().open();
                    }
                },
                key_shift_enter: function() {
                    var selected = that.options('selected');
                    if (selected.length) {
                        oml.UI.set({
                            item: selected[0],
                            itemView: 'book'
                        });
                    }
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
                        oml.$ui.previewDialog.updateElement();
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

    that.updateElement = function() {
        Ox.Request.clearCache('find');
        that.reloadList(true);
    };

    return that;

};