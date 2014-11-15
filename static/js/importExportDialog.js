'use strict';

oml.ui.importExportDialog = function(selected) {

    var ui = oml.user.ui,

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
                        id: 'hide',
                        title: Ox._('Hide')
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

    oml.getLists(function() {
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
            return list.user == '' && list.type != 'library' && (
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
            return list.user == '';
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
                        autocomplete: function(value, callback) {
                            oml.api.autocompleteFolder({path: value}, function(result) {
                                callback(result.data.items);
                            });
                        },
                        autocompleteSelect: true,
                        changeOnKeypress: true,
                        id: 'path',
                        label: 'Source Path',
                        labelWidth: 128,
                        width: 480
                    }),
                    Ox.SelectInput({
                        id: 'list',
                        inputValue: oml.getValidName(Ox._('Untitled'), getListNames()),
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
                            {id: 'copy', title: Ox._('Copy (keep files in source path)')},
                            {id: 'move', title: Ox._('Move (delete files from source path)')}
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
                            {id: 'add', title: Ox._('Add (keep all exisiting files in destination path)')},
                            {id: 'replace', title: Ox._('Replace (delete all existing files from destination path)')}
                        ],
                        label: Ox._('Export Mode'),
                        labelWidth: 128,
                        width: 480
                    })
                ]
            })
            .css({margin: '16px'})
            .bindEvent({
                change: function(data) {
                    var values = $form.values();
                    $activityButton[selected].options({
                        disabled: !values.path
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
                    var data = $form.values(),
                        addList = data.list && !Ox.contains(
                            oml.getOwnListNames(),
                            data.list
                        );
                    $innerPanel.replaceElement(0,
                        renderActivity({
                            activity: 'import',
                            path: data.path,
                            progress: [0, 0]
                        })
                    );
                    $label['export'].show();
                    (addList ? oml.addList : Ox.noop)(false, false, data.list, function(result) {
                        if (result) {
                            data.list = result.data.id
                        }
                        oml.api.import({
                            list: data.list,
                            mode: data.mode,
                            path: data.path,
                        }, function() {
                            // ...
                        });
                    });
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
        var progress = data.status ? 1
            : !data.progress[0] || !data.progress[1] ? -1
            : data.progress[0] / data.progress[1];
        $progress[data.activity] && $progress[data.activity].options({progress: progress})
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
                + ' ' + Ox._('{0} of {1}', [Ox.formatNumber(data.progress[0]), total])
            : '';
        $status[data.activity] && $status[data.activity].html(status);
    }

    that.select = function(selected_) {
        selected = selected_;
        $buttons.options({selected: selected});
        $innerPanel.options({selected: selected});
        return that;
    };

    oml.bindEvent({
        activity: function(data) {
            setProgress(data);
            setStatus(data);
            setButton(data);
        }
    });

    return that;

};
