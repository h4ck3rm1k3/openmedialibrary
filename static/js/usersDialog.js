'use strict';

oml.ui.usersDialog = function() {

    var preferences = oml.user.preferences,
        ui = oml.user.ui,

        that = Ox.Dialog({
            buttons: [
                Ox.Button({
                    id: 'preferences',
                    title: Ox._('Peering Preferences...')
                })
                .bindEvent({
                    click: function() {
                        oml.UI.set({
                            page: 'preferences',
                            'part.preferences': 'peering'
                        });
                    }
                }),
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
            content: Ox.Element(),
            fixedSize: true,
            height: 384,
            title: Ox._('Users'),
            width: 768
        })
        .bindEvent({
            close: function() {
                if (ui.page == 'users') {
                    oml.UI.set({page: ''});
                }
            },
            oml_page: function() {
                // ...
            }
        }),

        // FIXME: WRONG!
        $users = Ox.Element().css({background: 'rgb(240, 240, 240)'}),

        $user = Ox.Element(),

        $panel = Ox.SplitPanel({
            elements: [
                {element: $users, size: 256},
                {element: $user}
            ],
            orientation: 'horizontal'
        }),

        users,

        buttons = [
            {id: 'send', title: Ox._('Send')},
            {id: 'cancel', title: Ox._('Cancel')},
            {id: 'accept', title: Ox._('Accept')},
            {id: 'reject', title: Ox._('Reject')},
            {id: 'remove', title: Ox._('Remove...')}
        ],

        folders = [
            {
                id: 'peers',
                title: Ox._('Your Peers'),
                itemTitle: Ox._('No peers'),
                text: Ox._('You don\'t have any peers yet.')
            },
            {
                id: 'received',
                title: Ox._('Received Requests'),
                itemTitle: Ox._('No pending requests'),
                text: '...'
            },
            {
                id: 'sent',
                title: Ox._('Sent Requests'),
                itemTitle: Ox._('No pending requests'),
                text: '...'
            },
            {
                id: 'others',
                title: Ox._('Other Users'),
                itemTitle: Ox._('No other users'),
                text: Ox._('There are no other users in your extended network.')
            }
        ],

        $lists = [
            renderSectionList({id: 'invitations'}).appendTo($users)
        ],

        $folders = folders.map(function(folder) {
            return Ox.CollapsePanel({
                    collapsed: false,
                    title: folder.title
                })
                .css({width: '256px'})
                .appendTo($users);
        });

    function renderSectionList(folder) {

        var $list = Ox.TableList({
                columns: [
                    {
                        format: function() {
                            return $('<img>')
                                .attr({
                                    src: Ox.UI.getImageURL('symbolUser')
                                })
                                .css({
                                    width: '10px',
                                    height: '10px',
                                    margin: '2px -2px 2px 0',
                                    opacity: folder.id == 'invitations' ? 1 : 0.5
                                })
                        },
                        id: 'id',
                        visible: true,
                        width: 16
                    },
                    {
                        format: function(value) {
                            return folder.id == 'invitations'
                                ? value
                                : '<span class="OxLight">' + value + '</span>'
                        },
                        id: 'title',
                        visible: true,
                        width: 240
                    }
                ],
                items: [
                    {
                        id: folder.id,
                        title: folder.id == 'invitations' ? Ox._('Invitations')
                            : Ox.getObjectById(folders, folder.id).itemTitle
                    },
                ],
                sort: [{key: 'id', operator: '+'}],
                unique: 'id'
            })
            .css({height: '16px'})
            .bindEvent({
                select: function(data) {
                    if (data.ids.length) {
                        selectItem($list);
                        renderUser({section: data.ids[0]});
                    } else {
                        renderUser();
                    }
                }
            });

        $list.$body.css({height: '16px'}); // FIXME!

        return $list;

    }

    function renderUser(user) {

        Ox.print('renderUSER', user)

        var $user = Ox.Element(),

            $form = Ox.Element()
                .addClass('OxSelectable OxTextPage')
                .css({margin: '16px'})
                .appendTo($user),

            $warning = Ox.Element()
                .css({margin: '32px 16px'}) // FIXME: WTF!
                .appendTo($user),

            $id, $buttons = [], $message,

            folder;

        if (user && user.section) {
            folder = Ox.getObjectById(folders, user.section);
        }

        if (folder) {

            $('<div>')
                .html(folder.text)
                .appendTo($form);

        } else if (user) {

            if (user.section == 'invitations') {

                $('<div>')
                    .html(
                        'To invite someone, just send her your public key – that\'s all she\'ll need to add you as a peer. '
                        + 'Along with that, you may want to send a download link for Open Media Library, in case she doesn\'t have it yet.'
                    )
                    .appendTo($form);

                Ox.Input({
                        disabled: true,
                        label: Ox._('Your Public Key'),
                        labelWidth: 128,
                        value: oml.user.id,
                        width: 480
                    })
                    .css({
                        marginTop: '8px'
                    })
                    .appendTo($form);

                Ox.Input({
                        disabled: true,
                        label: Ox._('Download Link'),
                        labelWidth: 128,
                        value: 'https://openmedialibrary.com/#download',
                        width: 480
                    })
                    .css({
                        marginTop: '8px'
                    })
                    .appendTo($form);

                $('<div>')
                    .html(
                        'If someone invites you, or if you know another user\'s public key, you can add her here.'
                    )
                    .css({
                        margin: '32px 0 8px 0'
                    })
                    .appendTo($form);

            }

            Ox.Input({
                    label: Ox._('Nickname'),
                    labelWidth: 128,
                    placeholder: 'anonymous',
                    value: user.nickname || user.username || '',
                    width: 480
                })
                .bindEvent({
                    change: function(data) {
                        var value = oml.validateName(
                                data.value,
                                users.map(function(user) {
                                    return user.nickname;
                                })
                            );
                        this.value(value);
                        oml.api.editUser({
                            id: user.id,
                            nickname: value
                        }, function() {
                            // ...
                        });
                    }
                })
                .appendTo($form);

            if (user.section == 'invitations') {

                $id = Ox.Input({
                        label: Ox._('Public Key'),
                        labelWidth: 128,
                        width: 480
                    })
                    .bindEvent({
                        change: function(data) {
                            var isOwn = data.value == oml.user.id,
                                isPeer = Ox.contains(peerIds, data.value),
                                isValid = oml.validatePublicKey(data.value),
                                peer = Ox.getObjectById(users, data.value);
                            $sendButton.options({
                                disabled: isOwn || isPeer || !isValid
                            });
                            if (data.value && $sendButton.options('disabled')) {
                                $warning.html(
                                    isOwn ? 'That\'s your own public key.'
                                    : isPeer ? 'That\'s '
                                        + Ox.encodeHTMLEntities(peer.nickname || peer.username)
                                        + ' - you\'re already peered.'
                                    : 'That\'s not a valid key.'
                                )
                            } else {
                                $warning.empty();
                                if (data.value) {
                                    user.id = data.value;
                                }
                            }
                        }
                    })
                    .css({
                        marginTop: '8px'
                    })
                    .appendTo($form);

            } else {

                Ox.Input({
                        disabled: true,
                        label: Ox._('Username'),
                        labelWidth: 128,
                        placeholder: 'anonymous',
                        value: user.username || '',
                        width: 480
                    })
                    .css({
                        marginTop: '8px'
                    })
                    .appendTo($form);

                Ox.Input({
                        disabled: true,
                        label: Ox._('Contact'),
                        labelWidth: 128,
                        value: user.contact || '',
                        width: 480
                    })
                    .css({
                        marginTop: '8px'
                    })
                    .appendTo($form);

            }

            Ox.Label({
                    textAlign: 'center',
                    title: user.peered ? Ox._('Remove Peer')
                        : user.pending == 'received' ? Ox._('Peering Request')
                        : user.pending == 'sent' ? Ox._('Cancel Request')
                        : Ox._('Send Peering Request'),
                    width: 480
                })
                .css({
                    marginTop: '32px'
                })
                .appendTo($form);

            $message = Ox.Input({
                    label: Ox._('Message'),
                    labelWidth: 128,
                    placeholder: Ox._('none'),
                    width: 480
                })
                .css({
                    margin: '8px 0'
                })
                .appendTo($form);

            $buttons = (
                user.peered ? ['remove']
                : user.pending == 'received' ? ['accept', 'reject']
                : user.pending == 'sent' ? ['cancel']
                : ['send']
            ).map(function(id, index) {
                return Ox.Button({
                        title: Ox.getObjectById(buttons, id).title
                    })
                    .css({
                        float: 'right',
                        marginRight: index ? '8px' : 0
                    })
                    .bindEvent({
                        click: function() {
                            var data = {
                                id: user.id,
                                message: $message.value()
                            };
                            if (id == 'send') {
                                oml.api.requestPeering(data, function(result) {
                                    
                                });
                            } else if (id == 'cancel') {
                                oml.api.cancelPeering(data, function(result) {
                                    
                                });
                            } else if (id == 'accept') {
                                oml.api.acceptPeering(data, function(result) {
                                    
                                });
                            } else if (id == 'reject') {
                                oml.api.rejectPeering(data, function(result) {
                                    
                                });
                            } else if (id == 'remove') {
                                oml.ui.confirmDialog({
                                    buttons: [
                                        Ox.Button({
                                            title: Ox._('No, Keep Peer')
                                        }),
                                        Ox.Button({
                                            title: Ox._('Yes, Remove Peer')
                                        })
                                    ],
                                    title: Ox._('Remove Peering'),
                                    content: Ox._('Are you sure you want to remove this peer?')
                                }, function() {
                                    oml.api.removePeering(data, function(result) {
                                        // ...
                                    });
                                });
                            }
                        }
                    })
                    .appendTo($form);
            });

        }

        $panel.replaceElement(1, $user);

    }

    function renderUserList(folder) {

        var $list = Ox.TableList({
                columns: [
                    {
                        format: function(value, data) {
                            return oml.ui.statusIcon(
                                    value ? 'connected' : 'disconnected'
                                )
                                .css({
                                    margin: '2px 3px 3px 0'
                                });
                        },
                        id: 'online',
                        visible: true,
                        width: 16
                    },
                    {
                        format: function(value) {
                            return value
                                ? Ox.encodeHTMLEntities(value)
                                : '<span class="OxLight">anonymous</span>';
                        },
                        id: folder.id == 'peers' ? 'nickname' : 'username',
                        visible: true,
                        width: 240
                    }
                ],
                items: folder.items,
                max: 1,
                sort: [{key: 'index', operator: '+'}],
                sortable: folder.id == 'peers',
                unique: 'id'
            })
            .css({
                height: folder.items.length * 16 + 'px'
            })
            .bindEvent({
                select: function(data) {
                    if (data.ids.length) {
                        selectItem($list);
                        renderUser(Ox.getObjectById(users, data.ids[0]));
                    } else {
                        renderUser();
                    }
                }
            });

        return $list;

    }

    function selectItem($list, id) {
        $lists.forEach(function($element) {
            if ($element == $list) {
                $element.gainFocus();
            } else {
                $element.options({selected: []});
            }
        });
        if (id) {
            $list.options({selected: [id]});
            renderUser(Ox.getObjectById(users, id));
        }
    }

    function updateUsers() {
        // ...
    }

    that.update = function() {

        that.options({
            content: Ox.LoadingScreen().start()
        });

        oml.api.getUsers(function(result) {

            users = result.data.users;
            folders.forEach(function(folder) {
                folder.items = [];
            });
            users.forEach(function(user, index) {
                var id = user.peered ? 'peers' : (user.pending || 'others');
                Ox.getObjectById(folders, id).items.push(
                    Ox.extend({
                        index: index,
                        nickname: '',
                        username: ''
                    }, user)
                );
            });

            folders.forEach(function(folder, index) {
                $lists.push(
                    (
                        folder.items.length
                        ? renderUserList(folder)
                        : renderSectionList(folder)
                    ).appendTo($folders[index].$content)
                );
            });

            $lists.forEach(function($list, index) {
                $list.bindEvent({
                    selectnext: function() {
                        var $list;
                        if (index < $lists.length - 1) {
                            $list = $lists[index + 1];
                            selectItem($list, $list.options('items')[0].id);
                        }
                    },
                    selectprevious: function() {
                        var $list;
                        if (index) {
                            $list = $lists[index - 1];
                            selectItem($list, Ox.last($list.options('items')).id)
                        }
                    }
                })
            });

            that.options({content: $panel});

        });
        
        return that;

    };

    return that.update();

};