'use strict';

oml.ui.listDialog = function() {

    var ui = oml.user.ui,
        list = ui._list,

        that = Ox.Dialog({
            buttons: [].concat(list && !Ox.endsWith(list, ':') ? [
                Ox.Button({
                    id: 'duplicate',
                    title: Ox._('Duplicate List...')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                        oml.addList(list);
                    }
                })
            ] : []).concat(Ox.startsWith(list, ':') && list != '' ? [
                Ox.Button({
                    id: 'delete',
                    title: Ox._('Delete List...')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                        oml.ui.deleteListDialog().open();
                    }
                })
            ] : []).concat([
                {},
                Ox.Button({
                    id: 'done',
                    title: Ox._('Done')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                    }
                })
            ]),
            closeButton: true,
            content: Ox.LoadingScreen().start(),
            height: 264,
            title: Ox._('List – {0}', [
                ui._list == '' ? Ox._('All Libraries')
                : ui._list
                    .replace(/^:/, oml.user.preferences.username + ':')
                    .replace(/:$/, Ox._(':Library'))
            ]),
            width: 648 + Ox.UI.SCROLLBAR_SIZE
        });

    oml.api.getLists(function(result) {
        var lists = result.data.lists.filter(function(list) {
                return list.user == oml.user.preferences.username;
            }),
            listData = Ox.getObjectById(lists, list),
            listNames = lists.map(function(list) {
                return list.name;
            }),
            $content = Ox.Element()
                .css({margin: '16px'}),
            $nameInput = Ox.Input({
                    label: Ox._('Name'),
                    labelWidth: 128,
                    value: listData.name,
                    width: 616
                })
                .bindEvent({
                    change: function(data) {
                        var value = oml.validateName(data.value, listNames);
                        $nameInput.value(value);
                        oml.api.editList({
                            id: list,
                            name: value
                        }, function(result) {
                            oml.updateLists(function() {
                                oml.UI.set({
                                    find: {
                                        conditions: [{
                                            key: 'list',
                                            operator: '==',
                                            value: ':' + value
                                        }],
                                        operator: '&'
                                    }
                                });
                            });
                        });
                    }
                })
                .appendTo($content),
            $findForm;
        Ox.print('DEBUG:', list, listData)
        if (listData.type == 'smart') {
            $findForm = oml.ui.findForm(listData)
                .css({marginTop: '8px'})
                .appendTo($content);
        }
        that.options({content: $content});
    });

    return that;

};