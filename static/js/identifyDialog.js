'use strict';

oml.ui.identifyDialog = function(data) {

    var ui = oml.user.ui,

        ids = [
            'isbn10', 'isbn13', 'asin', 'lccn', 'oclc', 'olid'
        ].map(function(id) {
            return {
                id: id,
                title: Ox._(Ox.getObjectById(oml.config.itemKeys, id).title)
            };
        }),

        keys = [
            'title', 'author', 'publisher', 'date'
        ].map(function(id) {
            return {
                id: id,
                title: Ox._(Ox.getObjectById(oml.config.itemKeys, id).title)
            };
        }),

        $input = Ox.FormElementGroup({
                elements: [
                    Ox.Select({
                        items: ids,
                        overlap: 'right',
                        value: 'isbn10',
                        width: 128
                    }),
                    Ox.Input({
                        value: data['isbn10'] || '',
                        width: 610
                    })
                ]
            })
            .css({margin: '16px'}),

        $preview = Ox.Element(),

        $idPanel = Ox.SplitPanel({
            elements: [
                {element: Ox.Element().append($input), size: 48},
                {element: $preview}
            ],
            orientation: 'vertical'
        }),

        $form = Ox.Form({
                items: keys.map(function(key) {
                    return Ox.Input({
                        id: key.id,
                        labelWidth: 128,
                        label: key.title,
                        value: key == 'author'
                            ? (data[key.id] || []).join(', ')
                            : data[key.id],
                        width: 736
                    });
                })
            })
            .css({padding: '16px'})
            .bindEvent({
                change: function(data) {
                    Ox.print('FORM CHANGE', data);
                }
            }),

        $list = Ox.TableList({
                columns: [
                    {
                        id: 'index'
                    },
                    {
                        id: 'title',
                        visible: true,
                        width: 288,
                    },
                    {
                        id: 'author',
                        visible: true,
                        width: 224
                    },
                    {
                        id: 'publisher',
                        visible: true,
                        width: 160
                    },
                    {
                        id: 'date',
                        visible: true,
                        width: 96
                    }
                ],
                items: [],
                max: 1,
                sort: [{key: 'index', operator: '+'}],
                unique: 'index'
            })
            .bindEvent({
                select: function(data) {
                    $that.options('buttons')[1].options({
                        disabled: data.ids.length == 0
                    });
                }
            }),

        $titlePanel = Ox.SplitPanel({
            elements: [
                {element: Ox.Element().append($form), size: 120},
                {element: $list}
            ],
            orientation: 'vertical'
        }),

        $bar = Ox.Bar({size: 24}),

        $buttons = Ox.ButtonGroup({
                buttons: [
                    {id: 'id', title: Ox._('Look Up by ID')},
                    {id: 'title', title: Ox._('Find by Title')}
                ],
                selectable: true,
                selected: 'id'
            })
            .css({
                width: '768px',
                padding: '4px 0',
                textAlign: 'center'
            })
            .bindEvent({
                change: function(data) {
                    $innerPanel.options({selected: data.value});
                }
            })
            .appendTo($bar),

        $innerPanel = Ox.SlidePanel({
            elements: [
                {id: 'id', element: $idPanel},
                {id: 'title', element: $titlePanel}
            ],
            orientation: 'horizontal',
            selected: 'id',
            size: 768
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
                    id: 'dontupdate',
                    title: Ox._('No, Don\'t Update')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                    }
                }),
                Ox.Button({
                    disabled: true,
                    id: 'update',
                    title: Ox._('Yes, Update')
                })
                .bindEvent({
                    click: function() {
                        Ox.print('NOT IMPLEMENTED');
                        that.close();
                    }
                })
            ],
            closeButton: true,
            content: $outerPanel,
            fixedSize: true,
            height: 384,
            title: Ox._('Identify Book'),
            width: 768
        });

    return that;

};