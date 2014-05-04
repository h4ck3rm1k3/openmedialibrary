'use strict';

oml.ui.folders = function() {

    var ui = oml.user.ui,

        userIndex = {},

        $lists = [],

        that = Ox.Element()
            .css({
                //overflowX: 'hidden',
                //overflowY: 'auto',
            })
            .bindEvent({
                oml_find: selectList
            });

    $lists.push(
        oml.$ui.librariesList = oml.ui.folderList({
                items: [
                    {
                        id: '',
                        name: Ox._('All Libraries'),
                        type: 'libraries',
                        items: -1
                    }
                ]
            })
            .bindEvent({
                load: function() {
                    oml.api.find({query: getFind()}, function(result) {
                        oml.$ui.librariesList.value('', 'items', result.data.items);
                    });
                },
                open: function() {

                },
                select: function() {
                    oml.UI.set({find: getFind('')});
                    oml.$ui.librariesList.options({selected: ['']});
                },
                selectnext: function() {
                    oml.UI.set(Ox.extend(
                        {find: getFind(':')},
                        'showFolder.' + oml.user.preferences.username,
                        true
                    ));
                },
            })
            .css({height: '16px'})
            .appendTo(that)
    );
    oml.$ui.librariesList.$body.css({height: '16px'}); // FIXME!

    oml.$ui.folder = [];
    oml.$ui.libraryList = [];
    oml.$ui.folderList = [];

    oml.api.getUsers(function(result) {

        var peers = result.data.users.filter(function(user) {
            return user.peered;
        });

        oml.api.getLists(function(result) {

            Ox.print('GOT LISTS', result.data);

            var users = [
                    {
                        id: oml.user.id,
                        nickname: oml.user.preferences.username,
                        online: oml.user.online
                    }
                ].concat(peers),

                lists = result.data.lists;

            users.forEach(function(user, index) {

                var $content,
                    libraryId = (!index ? '' : user.nickname) + ':';

                userIndex[user.nickname] = index;

                oml.$ui.folder[index] = Ox.CollapsePanel({
                        collapsed: false,
                        extras: [
                            oml.ui.statusIcon(
                                !oml.user.online ? 'unknown'
                                : user.online ? 'connected'
                                : 'disconnected'
                            ),
                            {},
                            Ox.Button({
                                style: 'symbol',
                                title: 'info',
                                tooltip: Ox._(!index ? 'Preferences' : 'Profile'),
                                type: 'image'
                            })
                            .bindEvent({
                                click: function() {
                                    if (!index) {
                                        oml.UI.set({
                                            page: 'preferences',
                                            'part.preferences': 'account'
                                        });
                                    } else {
                                        oml.UI.set({page: 'users'})
                                    }
                                }
                            })
                        ],
                        title: Ox.encodeHTMLEntities(user.nickname)
                    })
                    .css({
                        width: ui.sidebarSize
                    })
                    .bindEvent({
                        toggle: function(data) {
                            oml.UI.set('showFolder.' + user.nickname, !data.collapsed);
                        }
                    })
                    .bindEvent(
                        'oml_showfolder.' + user.nickname.toLowerCase(),
                        function(data) {
                            oml.$ui.folder[index].options({collapsed: !data.value});
                        }
                    )
                    .appendTo(that);

                $content = oml.$ui.folder[index].$content
                    .css({
                        height: (1 + lists[user.id].length) * 16 + 'px'
                    });

                $lists.push(
                    oml.$ui.libraryList[index] = oml.ui.folderList({
                            items: [
                                {
                                    id: libraryId,
                                    name: Ox._('Library'),
                                    type: 'library',
                                    items: -1
                                }
                            ]
                        })
                        .bindEvent({
                            add: function() {
                                !index && oml.addList();
                            },
                            load: function() {
                                oml.api.find({
                                    query: getFind(libraryId)
                                }, function(result) {
                                    oml.$ui.libraryList[index].value(
                                        libraryId, 'items', result.data.items
                                    );
                                });
                            },
                            open: function() {
                                oml.$ui.listDialog = oml.ui.listDialog().open();
                            },
                            select: function(data) {
                                oml.UI.set({find: getFind(data.ids[0])});
                            },
                            selectnext: function() {
                                oml.UI.set({find: getFind(lists[user.id][0].id)});
                            },
                            selectprevious: function() {
                                var userId = !index ? null : users[index - 1].id,
                                    set = {
                                        find: getFind(
                                            !index
                                            ? ''
                                            : Ox.last(lists[userId]).id
                                        )
                                    };
                                if (userId) {
                                    Ox.extend(set, 'showFolder.' + userId, true);
                                }
                                oml.UI.set(set);
                            }
                        })
                        .appendTo($content)
                );

                $lists.push(
                    oml.$ui.folderList[index] = oml.ui.folderList({
                            draggable: !!index,
                            items: lists[user.id],
                            sortable: true
                        })
                        .bindEvent({
                            add: function() {
                                !index && oml.addList();
                            },
                            'delete': function() {
                                !index && oml.deleteList();
                            },
                            key_control_d: function() {
                                oml.addList(ui._list);
                            },
                            load: function() {
                                // ...
                            },
                            move: function(data) {
                                lists[user.id] = data.ids.map(function(listId) {
                                    return Ox.getObjectById(lists[user.id], listId);
                                });
                                oml.api.sortLists({
                                    ids: data.ids,
                                    user: user.id
                                }, function(result) {
                                    // ...
                                });
                            },
                            open: function() {
                                oml.ui.listDialog().open();
                            },
                            select: function(data) {
                                oml.UI.set({find: getFind(data.ids[0])});
                            },
                            selectnext: function() {
                                if (index < users.length - 1) {
                                    oml.UI.set(Ox.extend(
                                        {find: getFind(users[index + 1].nickname + ':')},
                                        'showFolder.' + users[index + 1].nickname,
                                        true
                                    ));
                                }
                            },
                            selectprevious: function() {
                                oml.UI.set({find: getFind(libraryId)});
                            }
                        })
                        .bindEvent(function(data, event) {
                            if (!index) {
                                Ox.print('LIST EVENT', event, data);
                            }
                        })
                        .css({height: lists[user.id].length * 16 + 'px'})
                        .appendTo($content)
                );

                oml.$ui.folderList[index].$body.css({top: '16px'});

            });

            selectList();

        });
    });

    function getFind(list) {
        return {
            conditions: list ? [{
                key: 'list',
                operator: '==',
                value: list
            }] : [],
            operator: '&'
        };
    }

    function selectList() {
        var split = ui._list.split(':'),
            index = userIndex[split[0] || oml.user.preferences.username],
            list = split[1],
            $selectedList = !ui._list ? oml.$ui.librariesList
                : !list ? oml.$ui[!list ? 'libraryList' : 'folderList'][index]
                : oml.$ui.folderList[index];
        $lists.forEach(function($list) {
            if ($list == $selectedList) {
                $list.options({selected: [ui._list]}).gainFocus();
            } else {
                $list.options({selected: []})
            }
        });
    }

    return that;

};