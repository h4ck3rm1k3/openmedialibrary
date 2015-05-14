'use strict';

oml.ui.titlesDialog = function() {

    var height = Math.round((window.innerHeight - 48) * 0.9),
        width = 512 + Ox.UI.SCROLLBAR_SIZE,

        $findInput = Ox.Input({
                changeOnKeypress: true,
                clear: true,
                placeholder: Ox._('Find'),
                width: 192
            })
            .css({float: 'right', margin: '4px'})
            .bindEvent({
                change: function(data) {
                    var query = {
                            conditions: [
                                {
                                    key: 'title',
                                    operator: '=',
                                    value: data.value
                                },
                                {
                                    key: 'sorttitle',
                                    operator: '=',
                                    value: data.value
                                }
                            ],
                            operator: '|'
                        };
                    $list.options({
                        query: query
                    });
                }
            }),

        $list = Ox.TableList({
                columns: [
                    {
                        id: 'id',
                        title: Ox._('ID'),
                        visible: false
                    },
                    {
                        id: 'title',
                        operator: '+',
                        removable: false,
                        title: Ox._('Title'),
                        visible: true,
                        width: 256
                    },
                    {
                        editable: true,
                        id: 'sorttitle',
                        operator: '+',
                        title: Ox._('Sort Title'),
                        visible: true,
                        width: 256
                    },
                ],
                columnsVisible: true,
                items: oml.api.findTitles,
                keys: [],
                max: 1,
                scrollbarVisible: true,
                sort: [{key: 'sorttitle', operator: '+'}],
                unique: 'id'
            })
            .bindEvent({
                init: function(data) {
                    $status.html(
                        Ox.toTitleCase(Ox.formatCount(data.items, 'title'))
                    );
                },
                open: function(data) {
                    $list.find('.OxItem.OxSelected > .OxCell.OxColumnSorttitle')
                        .trigger('mousedown')
                        .trigger('mouseup');
                },
                select: function(data) {
                    $findButton.options({disabled: !data.ids.length});
                },
                submit: function(data) {
                    Ox.Request.clearCache('findTitles');
                    oml.api.editTitle({
                        id: data.id,
                        sorttitle: data.value
                    });
                }
            }),

        $findButton = Ox.Button({
                disabled: true,
                title: Ox._('Find'),
                width: 48
            }).bindEvent({
                click: function() {
                    that.close();
                    oml.UI.set({find: {
                        conditions: [{
                            key: 'title',
                            value: $list.value(
                                $list.options('selected'), 'title'
                            ),
                            operator: '='
                        }],
                        operator: '&'
                    }});
                    oml.$ui.findElement.updateElement();
                }
            }),

        that = Ox.Dialog({
                buttons: [
                    Ox.Button({
                        title: Ox._('Sort Names...')
                    }).bindEvent({
                        click: function() {
                            that.close();
                            (oml.$ui.namesDialog || (
                                oml.$ui.namesDialog = oml.ui.namesDialog()
                            )).open();
                        }
                    }),
                    {},
                    $findButton,
                    Ox.Button({
                        title: Ox._('Done'),
                        width: 48
                    }).bindEvent({
                        click: function() {
                            that.close();
                        }
                    })
                ],
                closeButton: true,
                content: Ox.SplitPanel({
                    elements: [
                        {
                            element: Ox.Bar({size: 24})
                                .append($status)
                                .append(
                                    $findInput
                                ),
                            size: 24
                        },
                        {
                            element: $list
                        }
                    ],
                    orientation: 'vertical'
                }),
                height: height,
                maximizeButton: true,
                minHeight: 256,
                minWidth: 512,
                padding: 0,
                title: Ox._('Sort Titles'),
                width: width
            })
            .bindEvent({
                resizeend: function(data) {
                    var width = (data.width - Ox.UI.SCROLLBAR_SIZE) / 2;
                    [
                        {id: 'title', width: Math.ceil(width)},
                        {id: 'sorttitle', width: Math.floor(width)}
                    ].forEach(function(column) {
                        $list.resizeColumn(column.id, column.width);
                    });
                }
            }),

        $status = $('<div>')
            .css({
                position: 'absolute',
                top: '4px',
                left: '128px',
                right: '128px',
                bottom: '4px',
                paddingTop: '2px',
                fontSize: '9px',
                textAlign: 'center'
            })
            .appendTo(that.find('.OxButtonsbar'));

    return that;

};

