'use strict';

oml.ui.deleteListDialog = function() {

    var ui = oml.user.ui,

        that = oml.ui.confirmDialog({
            buttons: [
                Ox.Button({
                    title: Ox._('No, Keep List')
                }),
                Ox.Button({
                    title: Ox._('Yes, Delete List')
                })
            ],
            content: Ox._('Are you sure you want to delete this list?'),
            title: Ox._('Delete List')
        }, function() {
            oml.api.removeList({
                id: ui._list
            }, function() {
                oml.updateLists(function() {
                    oml.UI.set({
                        find: {
                            conditions: [{
                                key: 'list',
                                operator: '==',
                                value: ':'
                            }],
                            operator: '&'
                        }
                    });
                });
            });
        });

    return that;

};