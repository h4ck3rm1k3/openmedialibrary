'use strict';

oml.ui.mainMenu = function() {

    var ui = oml.user.ui,
        findState = oml.getFindState(ui.find),
        appItems = Ox.getObjectById(oml.config.pages, 'app').parts,

        that = Ox.MainMenu({
            extras: [
                oml.$ui.connectionButton = oml.ui.connectionButton(),
                oml.$ui.notificationsButton = oml.ui.notificationsButton(),
                oml.$ui.loadingIcon = oml.ui.loadingIcon()
            ],
            menus: [
                {
                    id: 'appMenu',
                    title: '<img src="/static/png/oml.png" style="width: 14px; height: 14px">',
                    items: [
                        appItems[0],
                        {}
                    ].concat(
                        appItems.slice(1, -1)
                    ).concat([
                        {},
                        Ox.last(appItems)
                    ])
                },
                {
                    id: 'userMenu',
                    title: Ox._('User'),
                    items: [
                        {
                            id: 'preferences',
                            title: Ox._('Preferences...'),
                            keyboard: 'control ,'
                        },
                        {},
                        {
                            id: 'users',
                            title: Ox._('Users...')
                        },
                        {
                            id: 'devices',
                            title: Ox._('Devices...')
                        }
                    ]
                },
                getListMenu(),
                getEditMenu(),
                {
                    id: 'viewMenu',
                    title: Ox._('View'),
                    items: [
                        {
                            id: 'section',
                            title: Ox._('Section'),
                            items: [
                                {
                                    group: 'section',
                                    min: 1,
                                    max: 1,
                                    items: [
                                        {
                                            id: 'books',
                                            title: Ox._('Books'),
                                            checked: true
                                        },
                                        {
                                            id: 'music',
                                            title: Ox._('Music'),
                                            disabled: true
                                        },
                                        {
                                            id: 'movies',
                                            title: Ox._('Movies'),
                                            disabled: true
                                        }
                                    ]
                                }
                            ]
                        },
                        {},
                        {
                            id: 'iconSubmenu',
                            title: 'Icons',
                            items: [
                                {
                                    group: 'icons',
                                    min: 1,
                                    max: 1,
                                    items: [
                                        {
                                            id: 'cover',
                                            title: Ox._('Cover'),
                                            checked: ui.icons == 'cover'
                                        },
                                        {
                                            id: 'preview',
                                            title: Ox._('Preview'),
                                            checked: ui.icons == 'preview'
                                        }
                                    ]
                                },
                                {},
                                {
                                    id: 'showfileinfo',
                                    title: 'Show File Info',
                                    checked: ui.showFileInfo
                                },
                                {},
                                {
                                    group: 'fileinfo',
                                    min: 1,
                                    max: 1,
                                    disabled: !ui.showFileInfo,
                                    items: [
                                        {
                                            id: 'extension',
                                            title: Ox._('Show Extension'),
                                            checked: ui.fileInfo == 'extension'
                                        },
                                        {
                                            id: 'size',
                                            title: Ox._('Show Size'),
                                            checked: ui.fileInfo == 'size'
                                        }
                                    ]
                                }
                            ]
                        },
                        {},
                        { 
                            id: 'showsidebar',
                            title: Ox._((ui.showSidebar ? 'Hide' : 'Show') + ' Sidebar'),
                            keyboard: 'shift s'
                        },
                        { 
                            id: 'showinfo',
                            title: Ox._((ui.showInfo ? 'Hide' : 'Show') + ' Info'),
                            keyboard: 'shift i',
                            disabled: !ui.showSidebar
                        },
                        { 
                            id: 'showfilters',
                            title: Ox._((ui.showFilters ? 'Hide' : 'Show') + ' Filters'),
                            keyboard: 'shift f',
                            disabled: !!ui.item 
                        },
                        { 
                            id: 'showbrowser',
                            title: Ox._((ui.showBrowser ? 'Hide': 'Show') + ' Browser'),
                            keyboard: 'shift b',
                            disabled: !ui.item
                        },
                        {},
                        {
                            id: 'notifications',
                            title: Ox._('Notifications...')
                        },
                        {
                            id: 'transfers',
                            title: Ox._('Transfers...')
                        },
                        {
                            id: 'activity',
                            title: Ox._('Activity...')
                        }
                    ]
                },
                {
                    id: 'sortMenu',
                    title: Ox._('Sort'),
                    items: [
                        {
                            id: 'sortitems',
                            title: Ox._('Sort Books by'),
                            items: [
                                {
                                    group: 'sort',
                                    title: Ox._('Sort Books by'),
                                    min: 1,
                                    max: 1,
                                    items: oml.config.sortKeys.map(function(key) {
                                        return {
                                            id: key.id,
                                            title: Ox._(key.title),
                                            checked: key.id == ui.listSort[0].key
                                        };
                                    })
                                }
                            ]
                        },
                        {
                            id: 'orderitems',
                            title: Ox._('Order Books'),
                            items: [
                                {
                                    group: 'order',
                                    min: 1,
                                    max: 1,
                                    items: [
                                        {
                                            id: 'ascending',
                                            title: Ox._('Ascending'),
                                            checked: ui.listSort[0].operator == '+'
                                        },
                                        {
                                            id: 'descending',
                                            title: Ox._('Descending'),
                                            checked: ui.listSort[0].operator == '-'
                                        }
                                    ],
                                }
                            ]
                        },
                        {
                            id: 'advancedsort',
                            title: Ox._('Advanced Sort'),
                            keyboard: 'shift control s',
                            disabled: true
                        }
                    ]
                },
                {
                    id: 'findMenu',
                    title: Ox._('Find'),
                    items: [
                        {
                            id: 'finditems',
                            title: Ox._('Find'),
                            items: [
                                {
                                    group: 'find',
                                    title: Ox._('Find'),
                                    min: 1,
                                    max: 1,
                                    items: oml.config.findKeys.map(function(key) {
                                        return {
                                            id: key.id,
                                            checked: key.id == findState.key,
                                            title: Ox._(key.title)
                                        };
                                    })
                                },
                            ]

                        },
                        {
                            id: 'advancedfind',
                            title: Ox._('Advanced Find'),
                            keyboard: 'shift control f'
                        }
                    ]
                },
                {
                    id: 'helpMenu',
                    title: Ox._('Help'),
                    items: [
                        {
                            id: 'gettingstarted',
                            title: 'Getting Started...'
                        },
                        {
                            id: 'help',
                            title: Ox._('{0} Help...', ['Open Media Library']),
                            keyboard: 'control ?'
                        },
                        {
                            id: 'documentation',
                            title: Ox._('Documentation...'),
                            keyboard: 'shift control ?'
                        }
                    ]
                },
                {
                    id: 'debugMenu',
                    title: Ox._('Debug'),
                    items: [
                        {
                            id: 'debugmode',
                            title: Ox._((
                                oml.localStorage('enableDebugMode')
                                ? 'Disable' : 'Enable'
                            ) + ' Debug Mode'),
                        },
                        {
                            id: 'eventlogging',
                            title: Ox._((
                                oml.localStorage('enableEventLogging')
                                ? 'Disable' : 'Enable'
                            ) + ' Event Logging'),
                        },
                        {},
                        {
                            id: 'changelog',
                            title: Ox._('Change Log...')
                        },
                        {
                            id: 'errorlog',
                            title: Ox._('Error Log...')
                        }
                    ]
                }
            ]
        })
        .bindKeyboard()
        .bindEvent({
            change: function(data) {
                var id = data.id,
                    value = Ox.isBoolean(data.checked)
                        ? data.checked : data.checked[0].id;
                if (id == 'icons') {
                    oml.UI.set({icons: value});
                } else if (id == 'showfileinfo') {
                    oml.UI.set({showFileInfo: value});
                } else if (id == 'fileinfo') {
                    oml.UI.set({fileInfo: value});
                } else {
                    Ox.print('MAIN MENU DOES NOT YET HANDLE', id);
                }
            },
            click: function(data) {
                var id = data.id;
                if (Ox.contains([
                    'about', 'faq', 'terms',
                    'development', 'contact', 'update'
                ], id)) {
                    oml.UI.set({'part.app': id});
                    oml.UI.set({page: 'app'});
                } else if (id == 'preferences') {
                    oml.UI.set({page: 'preferences'});
                } else if (id == 'users') {
                    oml.UI.set({page: 'users'});
                } else if (Ox.contains([
                    'newlist', 'newlistfromselection',
                    'newsmartlist', 'newsmartlistfromresults'
                ], id)) {
                    oml.addList(Ox.contains(id, 'smart'), Ox.contains(id, 'from'));
                } else if (id == 'duplicatelist') {
                    oml.addList(ui._list);
                } else if (id == 'editlist') {
                    oml.ui.listDialog.open();
                } else if (id == 'deletelist') {
                    oml.ui.deleteListDialog.open();
                } else if (id == 'showsidebar') {
                    oml.UI.set({showSidebar: !ui.showSidebar});
                } else if (id == 'showinfo') {
                    oml.UI.set({showInfo: !ui.showInfo});
                } else if (id == 'showfilters') {
                    oml.UI.set({showFilters: !ui.showFilters});
                } else if (id == 'showbrowser') {
                    oml.UI.set({showBrowser: !ui.showBrowser});
                } else if (id == 'transfers') {
                    oml.UI.set({page: 'transfers'});
                } else {
                    Ox.print('MAIN MENU DOES NOT YET HANDLE', id);
                }
            },
            key_control_comma: function() {
                if (!oml.hasDialogOrScreen()) {
                    oml.UI.set({page: 'preferences'});
                }
            },
            key_control_f: function() {
                if (!oml.hasDialogOrScreen()) {
                    if (ui._findState.key != 'advanced') {
                        setTimeout(function() {
                            oml.$ui.findInput.focusInput(true);
                        });
                    } else {
                        oml.$ui.filterDialog = oml.ui.filterDialog().open();
                    }
                }
            },
            key_shift_b: function() {
                ui.item && oml.UI.set({showBrowser: !ui.showBrowser});
            },
            key_shift_f: function() {
                !ui.item && oml.UI.set({showFilters: !ui.showFilters});
            },
            key_shift_i: function() {
                ui.showSidebar && oml.UI.set({showInfo: !ui.showInfo});
            },
            key_shift_s: function() {
                oml.UI.set({showSidebar: !ui.showSidebar});
            },
            oml_find: function() {
                that.replaceMenu('listMenu', getListMenu());
                that.replaceMenu('editMenu', getEditMenu());
                /*
                var action = Ox.startsWith(ui._list, ':') && ui._list != ':'
                    ? 'enableItem' : 'disableItem';
                that[
                    ui._list && !Ox.endsWith(ui._list, ':')
                    ? 'enableItem' : 'disableItem'
                ]('duplicatelist');
                that[action]('editlist');
                that[action]('deletelist');
                */
            },
            oml_item: function(data) {
                if (!!data.value != !!data.previousValue) {
                    that[data.value ? 'disableItem' : 'enableItem']('showfilters');
                    that[data.value ? 'enableItem' : 'disableItem']('showbrowser');
                }
            },
            oml_listselection: function(data) {
                that.replaceMenu('editMenu', getEditMenu());
            },
            oml_showbrowser: function(data) {
                that.setItemTitle('showbrowser', Ox._((data.value ? 'Hide' : 'Show') + ' Browser'));
            },
            oml_showfilters: function(data) {
                that.setItemTitle('showfilters', Ox._((data.value ? 'Hide' : 'Show') + ' Filters'));
            },
            oml_showinfo: function(data) {
                that.setItemTitle('showinfo', Ox._((data.value ? 'Hide' : 'Show') + ' Info'));
            },
            oml_showsidebar: function(data) {
                that.setItemTitle('showsidebar', Ox._((data.value ? 'Hide' : 'Show') + ' Sidebar'));
                that[data.value ? 'enableItem' : 'disableItem']('showinfo');
            },
        });

    function getEditMenu() {
        var listData = oml.getListData(),
            username = oml.user.preferences.username,
            selectionItems = ui.listSelection.length,
            selectionItemName = (
                selectionItems > 1 ? Ox.formatNumber(selectionItems) + ' ' : ''
            ) + Ox._(clipboardItems == 1 ? 'Book' : 'Books'),
            clipboardItems = oml.clipboard.items(),
            clipboardType = oml.clipboard.type(),
            clipboardItemName = !clipboardItems ? ''
                : (
                    clipboardItems > 1 ? Ox.formatNumber(clipboardItems) + ' ' : ''
                ) + Ox._(clipboardItems == 1 ? 'Book' : 'Books'),
            canSelect = !ui.item,
            canCopy = canSelect && selectionItems,
            canCut = canCopy && listData.editable,
            canPaste = listData.editable && clipboardItems,
            canAdd = canCopy && clipboardItems && clipboardItemType == ui.section,
            canDownload = listData.user != username && selectionItems,
            historyItems = oml.history.items(),
            undoText = oml.history.undoText(),
            redoText = oml.history.redoText();
        return {
            id: 'editMenu',
            title: Ox._('Edit'),
            items: [
                {
                    id: 'importitems',
                    title: Ox._('Import Books...')
                },
                {
                    id: 'exportitems',
                    title: Ox._('Export Books...')
                },
                {},
                {
                    id: 'download',
                    title: Ox._('Download {0}', [selectionItemName]),
                    disabled: !canDownload,
                    keyboard: 'control d'
                },
                {},
                {
                    id: 'selectall',
                    title: Ox._('Select All'),
                    disabled: !canSelect,
                    keyboard: 'control a'
                },
                {
                    id: 'selectnone',
                    title: Ox._('Select None'),
                    disabled: !canSelect,
                    keyboard: 'shift control a'
                },
                {
                    id: 'invertselection',
                    title: Ox._('Invert Selection'),
                    disabled: !canSelect,
                    keyboard: 'alt control a'
                },
                {},
                {
                    id: 'cut',
                    title: Ox._('Cut {0}', [selectionItemName]),
                    disabled: !canCut,
                    keyboard: 'control x'
                },
                {
                    id: 'cutadd',
                    title: Ox._('Cut and Add to Clipboard'),
                    disabled: !canCut || !canAdd,
                    keyboard: 'shift control x'
                },
                {
                    id: 'copy',
                    title: Ox._('Copy {0}', [selectionItemName]),
                    disabled: !canCopy,
                    keyboard: 'control c'
                },
                {
                    id: 'copyadd',
                    title: Ox._('Copy and Add to Clipboard'),
                    disabled: !canCopy || !canAdd,
                    keyboard: 'shift control c'
                },
                {
                    id: 'paste',
                    title: !clipboardItems ? Ox._('Paste') : Ox._('Paste {0}', [clipboardItemName]),
                    disabled: !canPaste,
                    keyboard: 'control v'
                },
                {
                    id: 'clearclipboard',
                    title: Ox._('Clear Clipboard'),
                    disabled: !clipboardItems
                },
                {},
                {
                    id: 'delete',
                    title: Ox._('Delete {0} from List', [selectionItemName]),
                    disabled: !canCut,
                    keyboard: 'delete'
                },
                {},
                {
                    id: 'undo',
                    title: undoText ? Ox._('Undo {0}', [undoText]) : Ox._('Undo'),
                    disabled: !undoText,
                    keyboard: 'control z'
                },
                {
                    id: 'redo',
                    title: redoText ? Ox._('Redo {0}', [redoText]) : Ox._('Redo'),
                    disabled: !redoText,
                    keyboard: 'shift control z'
                },
                {
                    id: 'clearhistory',
                    title: Ox._('Clear History'),
                    disabled: !historyItems,
                }
            ]
        };
    }

    function getListMenu() {
        var isLibraries = !ui._list,
            isLibrary = Ox.endsWith(ui._list, ':'),
            isList = !isLibraries && !isLibrary,
            isOwnList = ui._list[0] == ':';
        return {
            id: 'listMenu',
            title: Ox._('List'),
            items: [
                {
                    id: 'libraries',
                    title: Ox._('All Libraries'),
                    keyboard: 'shift control w'
                },
                {
                    id: 'library',
                    title: Ox._('This Library'),
                    disabled: isLibraries,
                    keyboard: isLibrary ? 'control w' : ''
                },
                {
                    id: 'list',
                    title: Ox._('This List'),
                    disabled: isLibrary,
                    keyboard: isLibrary ? '' : 'control w'
                },
                {},
                {
                    id: 'newlist',
                    title: Ox._('New List'),
                    keyboard: 'control n'
                },
                {
                    id: 'newlistfromselection',
                    title: Ox._('New List from Selection'),
                    keyboard: 'shift control n',
                    disabled: !ui.listSelection.length
                },
                {
                    id: 'newsmartlist',
                    title: Ox._('New Smart List'),
                    keyboard: 'alt control n'
                },
                {
                    id: 'newsmartlistfromresults',
                    title: Ox._('New Smart List from Results'),
                    keyboard: 'shift alt control n'
                },
                {},
                {
                    id: 'duplicatelist',
                    title: Ox._('Duplicate List'),
                    disabled: !isList
                },
                {
                    id: 'editlist',
                    title: Ox._('Edit List...'),
                    keyboard: 'return',
                    disabled: !isOwnList
                },
                {
                    id: 'deletelist',
                    title: Ox._('Delete List...'),
                    keyboard: 'delete',
                    disabled: !isOwnList
                }
            ]
        };
    }

    that.update = function() {
        return that.updateMenu('listMenu', getListMenu())
            .updateMenu('editMenu', getEditMenu());
    };

    return that;

};
