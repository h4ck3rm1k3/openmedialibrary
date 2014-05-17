'use strict';

oml.ui.importExportDialog = function(selected) {

    var ui = oml.user.ui,
        username = oml.user.preferences.username,

        $bar = Ox.Bar({size: 24}),

        $buttons = Ox.ButtonGroup({
                buttons: [
                    {id: 'import', title: Ox._('Import Books')},
                    {id: 'export', title: Ox._('Export Books')}
                ],
                min: 1,
                max: 1,
                selectable: true,
                selected: selected
            })
            .css({
                width: '768px',
                padding: '4px 0',
                textAlign: 'center'
            })
            .bindEvent({
                change: function(data) {
                    oml.UI.set({page: data.value});
                }
            })
            .appendTo($bar),

        $innerPanel = Ox.SlidePanel({
            elements: [
                {id: 'import', element: Ox.Element()},
                {id: 'export', element: Ox.Element()}
            ],
            orientation: 'horizontal',
            selected: selected,
            size: 512
        }),

        $outerPanel = Ox.SplitPanel({
            elements: [
                {element: $bar, size: 24},
                {element: $innerPanel}
            ],
            orientation: 'vertical'
        }),

        that = Ox.Dialog({
                buttons: [
                    Ox.Button({
                        id: 'close',
                        title: Ox._('Close')
                    })
                    .bindEvent({
                        click: function() {
                            that.close();
                        }
                    })
                ],
                closeButton: true,
                content: Ox.LoadingScreen().start(),
                height: 144,
                removeOnClose: true,
                title: Ox._('Import &amp; Export Books'),
                width: 512
            })
            .bindEvent({
                close: function() {
                    if (Ox.contains(['import', 'export'], ui.page)) {
                        oml.UI.set({page: ''});
                    }
                },
                oml_page: function(data) {
                    if (Ox.contains(['import', 'export'], data.value)) {
                        selected = data.value;
                        $buttons.options({selected: selected});
                        $innerPanel.options({selected: selected});
                    }
                }
            }),

        $label = {},
        $activityButton = {},
        $progress = {},
        $status = {},
        $progressButton = {};

    oml.getUsersAndLists(function() {
        oml.api.getActivity(function(result) {
            var isActive = !Ox.isEmpty(result.data),
                activity = result.data.activity;
            /*
            result.data = {
                path: '/Users/rolux/Desktop/Books',
                status: {},
                progress: [0,42]
            };
            */
            Ox.print(result.data, '!!!!!!!!')
            $innerPanel
                .replaceElement(0,
                    activity == 'import' ? renderActivity(result.data)
                    : renderForm('import', isActive)
                )
                .replaceElement(1, 
                    activity == 'export' ? renderActivity(result.data)
                    : renderForm('export', isActive)
                );
            that.options({content: $outerPanel});
        });
    });

    function getListItems(selected) {
        var lists = ui._lists.filter(function(list) {
            return list.user == username && list.type != 'library' && (
                selected == 'export' || list.type == 'static'
            );
        });
        return [
            {id: '', title: Ox._('Library')}
        ].concat(
            lists.length ? [{}] : []
        ).concat(
            lists.map(function(list) {
                return {id: list.name, title: list.name};
            })
        ).concat(selected == 'import' ? [
            {},
            {id: 'FIXME', title: Ox._('New List...')}
        ] : []);
    }

    function getListNames() {
        return ui._lists.filter(function(list) {
            return list.user == username;
        }).map(function(list) {
            return list.name;
        });
    }

    function renderActivity(data) {
        var $element = Ox.Element(),
            $title = $('<div>')
                .addClass('OxSelectable')
                .css({
                    margin: '16px 16px 4px 16px',
                    width: '480px',
                    height: '16px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                })
                .html(
                    Ox._(data.activity == 'import' ? 'Import from' : 'Export to') 
                    + ' <span class="OxMonospace">' + data.path + '</span>'
                )
                .appendTo($element);
        $progress[data.activity] = Ox.Progressbar({
                progress: -1,
                showTooltips: true,
                width: 480
            })
            .css({margin: '4px 16px'})
            .appendTo($element);
        $status[data.activity] = $('<div>')
            .addClass('OxSelectable')
            .css({
                margin: '6px 16px 4px 16px',
                height: '16px'
            })
            .appendTo($element);

        $progressButton[data.activity] = Ox.Button({
                title: '',
                width: 128
            })
            .css({
                position: 'absolute',
                right: '16px',
                bottom: '16px'
            })
            .bindEvent({
                click: function() {
                    if (this.options('title') == Ox._('Done')) {
                        $innerPanel.replaceElement(0, renderForm(data.activity));
                    } else {
                        oml.api[
                            data.activity == 'import' ? 'cancelImport' : 'cancelExport'
                        ](function() {
                            // ...
                        });
                    }
                }
            })
            .appendTo($element);
        if (data.progress) {
            setProgress(data);
            setStatus(data);
            setButton(data);
        }
        return $element;
    }

    function renderForm(selected, isActive) {
        var $element = Ox.Element(),
            $form = Ox.Form({
                items: selected == 'import' ? [
                    Ox.Input({
                        changeOnKeypress: true,
                        id: 'path',
                        label: 'Source Path',
                        labelWidth: 128,
                        width: 480
                    }),
                    Ox.SelectInput({
                        id: 'list',
                        inputValue: oml.validateName(Ox._('Untitled'), getListNames()),
                        inputWidth: 224,
                        items: getListItems('import'),
                        label: 'Destination',
                        labelWidth: 128,
                        max: 1,
                        min: 1,
                        value: '',
                        width: 480
                    }),
                    Ox.Select({
                        id: 'mode',
                        items: [
                            {id: 'copy', title: Ox._('Copy files')},
                            {id: 'move', title: Ox._('Move files')}
                        ],
                        label: Ox._('Import Mode'),
                        labelWidth: 128,
                        width: 480
                    })
                ] : [
                    Ox.Input({
                        changeOnKeypress: true,
                        id: 'path',
                        label: 'Destination Path',
                        labelWidth: 128,
                        width: 480
                    }),
                    Ox.Select({
                        id: 'list',
                        items: getListItems('export'),
                        label: 'Source',
                        labelWidth: 128,
                        value: ':',
                        width: 480
                    }),
                    Ox.Select({
                        id: 'mode',
                        items: [
                            {id: 'keep', title: Ox._('Keep existing files')},
                            {id: 'remove', title: Ox._('Remove existing files')}
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
                        if (data.data.value[0] != '') {
                            $form.values('list', oml.validateName(data.data.value, getListNames()))
                        }
                    }
                    $activityButton[selected].options({
                        disabled: !values.path //|| !values.list
                    });
                }
            })
            .appendTo($element);
        $label[selected] = Ox.Label({
                //textAlign: 'center',
                title: Ox._(
                    'Waiting for '
                    + (selected == 'import' ? 'export' : 'import')
                    + ' to finish...'
                ),
                width: 344
            })
            .css({
                position: 'absolute',
                bottom: '16px',
                left: '16px'
            })
            [isActive ? 'show' : 'hide']()
            .appendTo($element);
        $activityButton[selected] = Ox.Button({
                disabled: true,
                id: 'import',
                title: Ox._(selected == 'import' ? 'Import' : 'Export'),
                width: 128
            })
            .css({
                position: 'absolute',
                right: '16px',
                bottom: '16px'
            })
            .bindEvent({
                click: function() {
                    var data = $form.values();
                    $innerPanel.replaceElement(0,
                        renderActivity({
                            activity: 'import',
                            path: data.path,
                            progress: [0, 0]
                        })
                    );
                    $label['export'].show();
                    oml.api.import({
                        list: data.list, // FIXME: WRONG for Library
                        mode: data.mode,
                        path: data.path,
                    }, function() {
                        // ...
                    })
                }
            })
            .appendTo($element);
        return $element;
    }

    function setButton(data) {
        $progressButton[data.activity].options({
            title: !data.status ? Ox._(
                data.activity == 'import' ? 'Cancel Import' : 'Cancel Export'
            ) : Ox._('Done')
        });
    }

    function setProgress(data) {
        Ox.print('SET PROGRESS', data, $progress)
        var progress = data.status ? 1
            : !data.progress[0] || !data.progress[1] ? -1
            : data.progress[0] / data.progress[1];
        $progress[data.activity].options({progress: progress})
    }

    function setStatus(data) {
        // FIXME: LOCALIZATION
        var total = Ox.formatCount(data.progress[1], 'book').replace(/$no /, 'No'),
            status = data.status && data.status.code
            ? (
                data.status.code == 200 ? (
                    data.progress[1]
                    ? 'Done. ' + total + ' ' + (selected == 'import' ? 'imported' : 'exported.')
                    : Ox._('No books found.')
                )
                : data.status.code == 404 ? Ox._((
                    selected == 'import' ? 'Source' : 'Destination'
                ) + ' path not found.')
                : Ox._((selected == 'import' ? 'Import' : 'Export') + 'failed.')
            )
            : !data.progress[0] && data.progress[1] ? Ox._('Scanning: {0} found.', [total])
            : data.progress[0] ? Ox._(selected == 'import' ? 'Importing:' : 'Exporting')
                + ' ' + Ox._('{0} of {1}', [data.progress[0], total])
            : '';
        $status[data.activity].html(status);
    }

    that.select = function(selected_) {
        selected = selected_;
        $buttons.options({selected: selected});
        $innerPanel.options({selected: selected});
        return that;
    };

    oml.bindEvent({
        activity: function(data) {
            Ox.print('activity', arguments);
            setProgress(data);
            setStatus(data);
            setButton(data);
        }
    });

    return that;

};
