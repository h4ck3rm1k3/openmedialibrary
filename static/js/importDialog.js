'use strict';

oml.ui.importDialog = function() {

    var ui = oml.user.ui,
        username = oml.user.preferences.username,

        lists = ui._lists.filter(function(list) {
            return list.user == username && list.type == 'static';
        }),
        items = [
            {id: ':', title: Ox._('Library')}
        ].concat(
            lists.length ? [{}] : []
        ).concat(
            lists.map(function(list) {
                return {id: list.id, title: list.name};
            })
        ).concat([
            {},
            {id: '', title: Ox._('New List...')}
        ]),

        listNames = ui._lists.filter(function(list) {
            return list.user == username;
        }).map(function(list) {
            return list.name;
        }),

        $form = Ox.Form({
                items: [
                    Ox.Input({
                        changeOnKeypress: true,
                        id: 'path',
                        label: 'Source Path',
                        labelWidth: 128,
                        width: 480
                    }),
                    Ox.SelectInput({
                        id: 'list',
                        inputValue: oml.validateName(Ox._('Untitled'), listNames),
                        inputWidth: 224,
                        items: items,
                        label: 'Destination',
                        labelWidth: 128,
                        max: 1,
                        min: 1,
                        value: ':',
                        width: 480
                    }),
                    Ox.Select({
                        id: 'action',
                        items: [
                            {id: 'copy', title: Ox._('Keep files in source path')},
                            {id: 'move', title: Ox._('Remove files from source path')}
                        ],
                        label: Ox._('Import Mode'),
                        labelWidth: 128,
                        width: 480
                    })
                ]
            })
            .css({margin: '16px'})
            .bindEvent({
                change: function(data) {
                    var values = $form.values();
                    Ox.print('FORM CHANGE', data);
                    if (data.id == 'list') {
                        // FIXME: WRONG
                        if (data.data.value[0] != ':') {
                            $form.values('list', oml.validateName(data.data.value, listNames))
                        }
                    }
                    that[
                        values.path && values.list ? 'enableButton' : 'disableButton'
                    ]('import');
                }
            }),

        that = Ox.Dialog({
            buttons: [
                Ox.Button({
                    id: 'dontimport',
                    title: Ox._('No, Don\'t Import')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                    }
                }),
                Ox.Button({
                    disabled: true,
                    id: 'import',
                    title: Ox._('Yes, Import')
                })
                .bindEvent({
                    click: function() {
                        var data = $form.values();
                        oml.api.import({
                            path: data.path,
                            list: data.list == ':' ? null : data.list
                        }, function() {
                            // ...
                        })
                        that.close();
                    }
                })
            ],
            content: $form,
            height: 128,
            title: Ox._('Import Books'),
            width: 512
        });

    return that;

};