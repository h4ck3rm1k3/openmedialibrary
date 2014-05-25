'use strict';

oml.ui.preferencesDialog = function() {

    var preferences = oml.user.preferences,
        ui = oml.user.ui,

        items = {
            account: [
                {
                    id: 'username',
                    title: 'Username',
                    value: preferences.username,
                    help: 'Your username doesn\'t have to be your real name, and you can change it at any time. You can also leave it blank, in which case you will appear as "anonymous". Any characters other than colons and leading, trailing or consecutive spaces are okay.'
                },
                {
                    id: 'contact',
                    title: 'Contact',
                    value: preferences.contact,
                    help: 'This is a one-liner, visible to all your peers, that describes how to contact you. It can be an e-mail address, profile URL, IRC channel, postal address or anything else. It\'s also perfectly fine to leave this blank.'
                }
            ],
            library: [
                {
                    id: 'libraryPath',
                    title: 'Library Path',
                    autocomplete: function(value, callback) {
                        oml.api.autocompleteFolder({path: value}, function(result) {
                            callback(result.data.items);
                        });
                    },
                    autocompleteSelect: true,
                    value: preferences.libraryPath,
                    help: 'The directory in which your "Books" folder is located. This is where your media files are stored. It can be on your local machine, but just as well on an external drive or networked volume.'
                },
                {
                    id: 'importPath',
                    title: 'Import Path',
                    autocomplete: function(value, callback) {
                        oml.api.autocompleteFolder({path: value}, function(result) {
                            callback(result.data.items);
                        });
                    },
                    autocompleteSelect: true,
                    value: preferences.importPath,
                    help: 'Any media files that you put in this folder will be added to your library. Once added, they will be removed from this folder.'
                }
            ],
            peering: [
                {
                    id: 'sendRequests',
                    title: 'Send Requests',
                    value: preferences.sendRequests,
                    items: [
                        {id: 'manually', title: 'Manually'},
                        {id: 'automatically', title: 'Automatically'}
                    ],
                    help: 'By default, sending peering requests (to users that your peers are peered with) is done manually, but you can also automate this.'
                },
                {
                    id: 'receivedRequests',
                    title: 'Received Requests',
                    value: preferences.peeringRequests,
                    items: [
                        {id: 'notify', title: 'Notify Me'},
                        {id: 'accept', title: 'Accept All'},
                        {id: 'reject', title: 'Reject All'}
                    ],
                    help: 'Here you can set what happens when you receive a peering request. "Notify Me" is a good default, but maybe you think differently.'
                },
                {
                    id: 'acceptMessage',
                    title: 'Accept Message',
                    value: preferences.acceptMessage,
                    help: 'This is the default message you send whenever you accept a peering request. You can review it when accepting a request manually, and you can also leave it blank.'
                },
                {
                    id: 'rejectMessage',
                    title: 'Reject Message',
                    value: preferences.rejectMessage,
                    help: 'This is the default message you send whenever you reject a peering request. You can review it when rejecting a request manually, and you can also leave this blank.'
                },
            ],
            network: [
                {
                    id: 'downloadRate',
                    title: 'Download Rate',
                    value: preferences.downloadRate,
                    unit: 'KB/s',
                    help: 'Here you can set your bandwidth limits for file transfers. Leaving this blank means no limit.'
                },
                {
                    id: 'uploadRate',
                    title: 'Upload Rate',
                    value: preferences.uploadRate,
                    unit: 'KB/s',
                    help: 'Here you can set your bandwidth limits for file transfers. Leaving this blank means no limit.'
                }
            ],
            appearance: [
                {
                    id: 'theme',
                    title: 'Theme',
                    value: ui.theme,
                    items: oml.config.themes.map(function(theme) {
                        return {id: theme, title: Ox.Theme.getThemeData(theme).themeName};
                    }),
                    help: 'More themes are on their way. Also, you can contribute.'
                },
                {
                    id: 'locale',
                    title: 'Language',
                    value: ui.locale,
                    items: oml.config.locales.map(function(locale) {
                        return {id: locale, title: Ox.LOCALE_NAMES[locale]}
                    }),
                    help: 'More languages are on their way. Also, you can contribute.'
                },
                {
                    id: 'resetUI',
                    title: 'Reset UI Settings...',
                    click: function() {
                        oml.$ui.resetUIDialog = oml.ui.resetUIDialog().open();
                    },
                    help: 'This will reset the user interface to its default settings. This affects the size of various elements, your current selection of items, the application\'s theme and language, etc.'
                }
            ],
            extensions: [
                {
                    id: 'extensions',
                    title: 'Extensions',
                    value: preferences.extensions,
                    type: 'textarea',
                    help: 'If you want to write plug-ins to extend the functionality of Open Media Library, this is how. Any JavaScript you enter here will run on load. In case you ever need to temporarily disable extensions, press X once you see the loading screen.'
                }
            ],
            advanced: [
                {
                    id: 'showDebugMenu',
                    title: 'Show Debug Menu',
                    value: ui.showDebugMenu,
                    help: 'This enables the Debug Menu, which provides access to various profiling tools that you\'re probably not going to need, unless you\'re really curious.'
                },
                {
                    id: 'sendDiagnostics',
                    title: 'Send Diagnostics Data',
                    value: preferences.sendDiagnostics,
                    help: 'If enabled, this will periodically send a list of JavaScript errors and server errors – and nothing else – to openmedialibrary.com. It still comes with your IP address and your browser\'s user agent string, so if you don\'t want to share that, just leave this turned off.'
                }
            ]
        },

        $list = Ox.TableList({
            columns: [
                {
                    id: 'title',
                    visible: true,
                    width: 128 - Ox.UI.SCROLLBAR_SIZE
                }
            ],
            items: Ox.getObjectById(
                oml.config.pages, 'preferences'
            ).parts.map(function(part, index) {
                return {
                    id: part.id,
                    index: index,
                    title: Ox._(part.title)
                };
            }),
            max: 1,
            min: 1,
            scrollbarVisible: true,
            selected: [ui.part.preferences],
            sort: [{key: 'index', operator: '+'}],
            unique: 'id'
        })
        .bindEvent({
            select: function(data) {
                oml.UI.set({'part.preferences': data.ids[0]});
            }
        }),

        $main = Ox.Element()
            .addClass('OxTextPage OxSelectable'),

        $formElement = Ox.Element()
            .appendTo($main),

        $formLabel = Ox.Label({
                width: 512
            })
            .hide()
            .appendTo($formElement),

        $helpElement = Ox.Element()
            .css({
                position: 'absolute',
                right: '16px',
                top: '16px',
                width: '192px'
            })
            .hide()
            .appendTo($main),

        $helpLabel = Ox.Label({
            width: 176
        }),

        $closeButton = Ox.Button({
                overlap: 'left',
                title: 'close',
                tooltip: Ox._('Hide'),
                type: 'image'
            })
            .bindEvent({
                click: function() {
                    $helpElement.hide();
                }
            }),

        $helpTitle = Ox.FormElementGroup({
                elements: [
                    $helpLabel,
                    $closeButton
                ],
                float: 'right'
            })
            .appendTo($helpElement),

        $help = Ox.Element()
            .css({
                position: 'absolute',
                top: '24px'
            })
            .appendTo($helpElement),

        $panel = Ox.SplitPanel({
            elements: [
                {element: $list, size: 128},
                {element: $main}
            ],
            orientation: 'horizontal'
        }),
    
        $usersButton = Ox.Button({
                id: 'users',
                title: Ox._('Users...')
            })
            .bindEvent({
                click: function() {
                    oml.UI.set({page: 'users'});
                }
            }),

        $notificationsButton = Ox.Button({
                id: 'notifications',
                title: Ox._('Notifications...')
            })
            .bindEvent({
                click: function() {
                    oml.UI.set({page: 'notifications'});
                }
            }),

        $transfersButton = Ox.Button({
                id: 'transfers',
                title: Ox._('Transfers...')
            })
            .bindEvent({
                click: function() {
                    oml.UI.set({page: 'transfers'});
                }
            }),

        that = Ox.Dialog({
            buttons: [
                $usersButton,
                $notificationsButton,
                $transfersButton,
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
            ],
            closeButton: true,
            content: $panel,
            fixedSize: true,
            height: 384,
            keys: {escape: 'close'},
            removeOnClose: true,
            title: Ox._('Preferences'),
            width: 768
        })
        .bindEvent({
            open: function() {
                $list.gainFocus();
            },
            close: function() {
                if (ui.page == 'preferences') {
                    oml.UI.set({page: ''});
                }
            },
            'oml_part.preferences': function() {
                if (ui.page == 'preferences') {
                    that.updateElement();
                }
            }
        });

    function displayHelp(item) {
        $helpLabel.options({title: item.title});
        $help.html(Ox._(item.help));
        $helpElement.show();
    }

    that.updateElement = function() {

        var $form,
            $formTitle,
            part = ui.part.preferences,
            formItems = items[part];

        if (formItems[0].type == 'textarea') {
            $formTitle = Ox.FormElementGroup({
                elements: [
                    Ox.Label({
                        title: Ox._(formItems[0].title),
                        width: 384
                    }),
                    Ox.Button({
                        overlap: 'left',
                        title: 'help',
                        type: 'image'
                    })
                    .bindEvent({
                        click: function() {
                            displayHelp(formItems[0]);
                        }
                    })
                ],
                float: 'right'
            })
            .css({
                position: 'absolute',
                left: '16px',
                top: '16px'
            });
        }

        $form = Ox.Form({
            items: formItems.map(function(item) {
                return Ox.FormElementGroup({
                    elements: [
                        item.click
                        ? Ox.Button({
                            title: Ox._(item.title),
                            width: 256
                        })
                        .bindEvent({
                            click: item.click
                        })
                        : item.items
                        ? Ox.Select({
                            items: item.items,
                            label: Ox._(item.title),
                            labelWidth: 128,
                            value: item.value,
                            width: 384 - !!item.unit * 48
                        })
                        : item.type == 'textarea'
                        ? Ox.Input({
                            height: 328,
                            type: 'textarea',
                            value: oml.user.preferences[item.id] || item.value,
                            width: 400
                        })
                        : Ox.isBoolean(item.value)
                        ? Ox.Checkbox({
                            title: Ox._(item.title),
                            value: item.value,
                            width: 384
                        })
                        : Ox.Input({
                            autocomplete: item.autocomplete || null,
                            autocompleteSelect: item.autocompleteSelect || false,
                            label: Ox._(item.title),
                            labelWidth: 128,
                            placeholder: item.placeholder || '',
                            value: oml.user.preferences[item.id] || item.value || '',
                            width: 384 - !!item.unit * 48
                        })

                    ].concat(item.unit ? [
                        Ox.Label({
                            overlap: 'left',
                            title: item.unit,
                            width: 48
                        })
                    ] : []).concat(item.type != 'textarea' ? [
                        Ox.Button({
                            overlap: 'left',
                            title: 'help',
                            type: 'image'
                        })
                        .bindEvent({
                            click: function() {
                                displayHelp(item);
                            }
                        })
                    ] : []),
                    float: 'right',
                    id: item.id
                });
            })
        })
        .css({
            position: 'absolute',
            left: '16px',
            top: $formTitle ? '40px' : '16px'
        })
        .bindEvent({
            change: function(data) {
                var key = data.id,
                    value = data.data.value[0];
                if (key == 'username') {
                    value = oml.getValidName(value, [], ':');
                }
                if (key in oml.config.user.preferences) {
                    oml.Preferences.set(key, value);
                } else {
                    oml.UI.set(key, value);
                }
                if (key == 'theme') {
                    Ox.Theme(value);
                }
            }
        });

        $formElement.empty();
        $formTitle && $formElement.append($formTitle); 
        $formElement.append($form);
        $helpElement.hide();

        $usersButton[part == 'peering' ? 'show' : 'hide']();
        $notificationsButton[part == 'peering' ? 'show' : 'hide']();
        $transfersButton[part == 'network' ? 'show' : 'hide']();

        return that;

    };

    return that.updateElement();

};
