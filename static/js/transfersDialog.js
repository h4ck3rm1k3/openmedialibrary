'use strict';

oml.ui.transfersDialog = function() {

    var ui = oml.user.ui,

        $list = Ox.TableList({
            columns: [
                'id', 'title', 'extension', 'size',
                'transferadded', 'transferprogress'
            ].map(function(id) {
                var key = Ox.getObjectById(oml.config.itemKeys, id);
                return {
                    align: Ox.contains([
                        'size', 'transferprogress'
                    ], id) ? 'right' : 'left',
                    format: key.format,
                    id: id,
                    operator: oml.getSortOperator(id),
                    title: Ox._(key.title),
                    visible: id != 'id',
                    width: id == 'title' ? 240
                        : id == 'transferadded' ? 144
                        : id == 'transferprogress' ? 80 - Ox.UI.SCROLLBAR_SIZE
                        : key.columnWidth
                };
            }),
            columnsVisible: true,
            items: function(data, callback) {
                Ox.Request.clearCache('find'); // FIXME: not ideal - and doesn't work
                oml.api.find(Ox.extend(data, {
                    query: {
                        conditions: [{
                            key: 'mediastate',
                            operator: '==',
                            value: 'transferring'
                        }],
                        operator: '&'
                    }
                }), callback);
            },
            keys: ['author'],
            scrollbarVisible: true,
            sort: [{key: 'transferprogress', operator: '-'}],
            unique: 'id'
        }),

        $statusbar = Ox.Bar({size: 16}),

        $panel = Ox.SplitPanel({
            elements: [
                {element: $list},
                {element: $statusbar, size: 16}
            ],
            orientation: 'vertical'
        }),

        $item = Ox.Element(),

        $cancelButton = Ox.Button({
                title: 'Cancel Transfer...',
                width: 128
            })
            .css({
                margin: '8px'
            })
            .bindEvent({
                click: function() {
                    var ids = $list.options('selected');
                    ids && ids.length && oml.api.cancelDownloads({
                        ids: ids
                    }, function() {
                        $list.reloadList(true);
                    });
                }
            })
            .appendTo($item),

        $content = Ox.SplitPanel({
            elements: [
                {element: $panel},
                {element: $item, size: 160}
            ],
            orientation: 'horizontal'
        }),

        that = Ox.Dialog({
                buttons: [
                    Ox.Button({
                        id: 'preferences',
                        title: Ox._('Network Preferences...')
                    })
                    .bindEvent({
                        click: function() {
                            oml.UI.set({page: 'transfers'});
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
                content: $content,
                height: 384,
                title: Ox._('Transfers'),
                width: 768
            })
            .bindEvent({
                close: function() {
                    if (ui.page == 'transfers') {
                        oml.UI.set({page: ''});
                    }
                }
            });

    oml.bindEvent({
        transfer: Ox.throttle(function(data) {
            var current = $list.value(data.id);
            if (!Ox.isEmpty(current)  && current.transferprogress != data.progress) {
                $list.value(data.id, 'transferprogress', data.progress);
            }
        }, 1000)
    });

    return that;
    
};
