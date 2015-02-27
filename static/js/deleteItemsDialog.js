'use strict';

oml.ui.deleteItemsDialog = function() {

    var ui = oml.user.ui,

        items = ui.listSelection,
        itemsName = Ox._(items.length == 1 ? 'Item' : 'Items'),
        theseItemsName = items.length == 1
            ? Ox._('this item')
            : Ox._('these {0} items', [Ox.formatNumber(items.length)]),

        that = oml.ui.confirmDialog({
            buttons: [
                Ox.Button({
                    title: Ox._('No, Keep {0}', [itemsName])
                }),
                Ox.Button({
                    title: Ox._('Yes, Delete {0}', [itemsName])
                })
            ],
            content: Ox._('Are you sure that you want to permanently delete {0}?', [theseItemsName]),
            title: Ox._('Delete {0}', [itemsName])
        }, function() {
            oml.api.remove({
                ids: items
            }, function() {
                oml.UI.set({listSelection: []});
                Ox.Request.clearCache(); // to much?
                oml.$ui.list.updateElement();
                oml.user.ui.item && oml.UI.set({
                    item: '',
                    itemView: 'info'
                });
            });
        });

    return that;

};
