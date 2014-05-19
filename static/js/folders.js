'use strict';

oml.ui.folders = function() {

    var ui = oml.user.ui,
        username = oml.user.preferences.username,

        userIndex,
        users,

        $lists,

        that = Ox.Element()
            .css({
                overflowX: 'hidden',
                //overflowY: 'auto',
            })
            .bindEvent({
                oml_find: selectList
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

    function getFolderList(list) {
        var index = users.map(function(user) {
            return user.nickname;
        }).indexOf(list.user);
        return list.id == '' ? oml.$ui.librariesList
            : Ox.endsWith(list.id, ':') ? oml.$ui.libraryList[index]
            : oml.$ui.folderList[index];
    }

    function getUsersAndLists(callback) {
        oml.getUsers(function() {
            users = arguments[0];
            oml.getLists(function(lists) {
                callback(users, lists);
            });
        });
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

    that.updateElement = function() {

        that.empty();

        $lists = [];

        oml.$ui.folder = [];
        oml.$ui.libraryList = [];
        oml.$ui.folderList = [];

        getUsersAndLists(function(users, lists) {

            Ox.print('GOT USERS AND LISTS', users, lists);
            userIndex = {};

            $lists.push(
                oml.$ui.librariesList = oml.ui.folderList({
                        items: [
                            {
                                id: '',
                                name: Ox._('All Libraries'),
                                type: 'libraries',
                                items: Ox.getObjectById(lists, '').items
                            }
                        ]
                    })
                    .bindEvent({
                        select: function() {
                            oml.UI.set({find: getFind('')});
                            oml.$ui.librariesList.options({selected: ['']});
                        },
                        selectnext: function() {
                            oml.UI.set(Ox.extend(
                                {find: getFind(':')},
                                'showFolder.' + username,
                                true
                            ));
                        },
                    })
                    .css({height: '16px'})
                    .appendTo(that)
            );
            oml.$ui.librariesList.$body.css({height: '16px'}); // FIXME!

            users.forEach(function(user, index) {

                var $content,
                    items = lists.filter(function(list) {
                        return list.user == user.nickname
                            && list.type != 'library';
                    }),
                    libraryId = (!index ? '' : user.nickname) + ':'

                userIndex[user.nickname] = index;

                oml.$ui.folder[index] = Ox.CollapsePanel({
                        collapsed: false,
                        extras: [
                            oml.ui.statusIcon(user, index),
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
                        height: (1 + items.length) * 16 + 'px'
                    });

                $lists.push(
                    oml.$ui.libraryList[index] = oml.ui.folderList({
                            items: [
                                {
                                    id: libraryId,
                                    name: Ox._('Library'),
                                    type: 'library',
                                    items: Ox.getObjectById(lists, libraryId).items
                                }
                            ]
                        })
                        .bindEvent({
                            add: function() {
                                !index && oml.addList();
                            },
                            select: function(data) {
                                oml.UI.set({find: getFind(data.ids[0])});
                            },
                            selectnext: function() {
                                oml.UI.set({find: getFind(items[0].id)});
                            },
                            selectprevious: function() {
                                // FIXME: ugly
                                var set, user, userLists;
                                if (!index) {
                                    set = {find: getFind('')};
                                } else {
                                    user = users[index - 1].nickname;
                                    userLists = lists.filter(function(list) {
                                        return list.user == user;
                                    });
                                    set = {find: getFind(
                                        !userLists.length ? (user == oml.user.preferences.username ? '' : user) + ':'
                                        : Ox.last(userLists).id
                                    )};
                                    Ox.extend(set, 'showFolder.' + user, true);
                                }
                                oml.UI.set(set);
                            }
                        })
                        .appendTo($content)
                );

                $lists.push(
                    oml.$ui.folderList[index] = oml.ui.folderList({
                            draggable: !!index,
                            items: items,
                            sortable: !index
                        })
                        .bindEvent({
                            add: function() {
                                !index && oml.addList();
                            },
                            'delete': function() {
                                !index && oml.ui.deleteListDialog().open();
                            },
                            key_control_d: function() {
                                oml.addList(ui._list);
                            },
                            move: function(data) {
                                lists[user.id] = data.ids.map(function(listId) {
                                    return Ox.getObjectById(items, listId);
                                });
                                oml.api.sortLists({
                                    ids: data.ids,
                                    user: user.id
                                }, function(result) {
                                    // ...
                                });
                            },
                            open: function() {
                                !index && oml.ui.listDialog().open();
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
                        .css({height: items.length * 16 + 'px'})
                        .appendTo($content)
                );

                oml.$ui.folderList[index].$body.css({top: '16px'});

            });

            selectList();

        });

        return that;

    };

    that.updateItems = function(items) {
        Ox.print('UPDATE ITEMS', items);
        var $list;
        if (arguments.length == 0) {
            oml.getLists(function(lists) {
                lists.forEach(function(list) {
                    $list = getFolderList(list);
                    if ($list) {
                        $list.value(list.id, 'items', list.items);
                    }
                });
            });
        } else {
            $list = $lists.filter(function($list) {
                return $list.options('selected').length;
            })[0];
            if ($list && !Ox.isEmpty($list.value(ui._list))) {
                $list.value(ui._list, 'items', items);
            }
        }
    };

    that.updateOwnLists = function(callback) {
        oml.getLists(function(lists) {
            var items = lists.filter(function(list) {
                return list.user == oml.user.preferences.username
                    && list.type != 'library';
            });
            oml.$ui.folder[0].$content
                .css({height: 16 + items.length * 16 + 'px'});
            oml.$ui.folderList[0].options({
                    items: items
                })
                .css({height: items.length * 16 + 'px'})
                .size();
            callback && callback();
        });
    };

    oml.bindEvent({
        activity: function(data) {
            if (data.activity == 'import') {
                that.updateItems();
            }
        },
        'peering.accept': function(data) {
            that.updateElement();
        },
        'peering.remove': function(data) {
            that.updateElement();
        }
    });

    return that.updateElement();

};
