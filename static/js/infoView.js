'use strict';

oml.ui.infoView = function() {

    var ui = oml.user.ui,

        that = Ox.Element()
            .addClass('OxTextPage')
            .css({overflowY: 'auto'})
            .bindEvent({
                oml_item: function() {
                    if (ui.item) {
                        that.update(ui.item);
                    }
                },
                oml_listselection: function(data) {
                    if (data.value && data.value.length) {
                        that.update(data.value[0]);
                    }
                }
            }),

        $identifyPanel = Ox.SplitPanel({
                elements: [
                    {element: Ox.Element(), size: 120},
                    {element: Ox.Element()}
                ],
                orientation: 'vertical'
            }),

        $identifyDialog = Ox.Dialog({
            buttons: [
                Ox.Button({
                    id: 'dontupdate',
                    title: Ox._('No, Don\'t Update')
                })
                .bindEvent({
                    click: function() {
                        $identifyDialog.close();
                    }
                }),
                Ox.Button({
                    disabled: true,
                    id: 'update',
                    title: Ox._('Yes, Update')
                })
                .bindEvent({
                    click: function() {
                        $identifyDialog.close();
                    }
                })
            ],
            closeButton: true,
            content: $identifyPanel,
            fixedSize: true,
            height: 384,
            //removeOnClose: true,
            title: Ox._('Identify Book'),
            width: 768
        }),

        $cover = Ox.Element()
            .css({
                position: 'absolute',
                left: '16px',
                top: '16px',
                width: '256px'
            })
            .appendTo(that),

        $info = Ox.Element()
            .addClass('OxSelectable')
            .css({
                position: 'absolute',
                left: '288px',
                right: '176px',
                top: '16px'
            })
            .appendTo(that),

        $data = Ox.Element()
            .addClass('OxSelectable')
            .css({
                position: 'absolute',
                right: '16px',
                top: '16px',
                width: '128px'
            })
            .appendTo(that);

    function identify(data) {
        var $form = Ox.Form({
                    items: [
                        'title', 'author', 'publisher', 'date'
                    ].map(function(key) {
                        return Ox.Input({
                            id: key,
                            labelWidth: 128,
                            label: Ox.getObjectById(oml.config.itemKeys, key).title,
                            value: key == 'author' ? (data[key] || []).join(', ') : data[key],
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
                        $identifyDialog.options('buttons')[1].options({
                            disabled: data.ids.length == 0
                        });
                    }
                });
        $identifyPanel.replaceElement(0, $form);
        $identifyPanel.replaceElement(1, $list);
        $identifyDialog.open();
        identify(data);
        function identify(data) {
            oml.api.identify(data, function(result) {
                $list.options({
                    items: result.data.items.map(function(item, index) {
                        return Ox.extend(item, {index: index});
                    })
                });
            });
        }
    }

    function renderMediaButton(data) {
        return data.mediastate == 'unavailable'
            ? Ox.FormElementGroup({
                elements: [
                    Ox.Button({
                        title: Ox._('Download Book'),
                        width: 112
                    })
                    .bindEvent({
                        click: function() {
                            data.mediastate = 'transferring';
                            that.update(data, $data);
                            oml.api.download({id: ui.item}, function(result) {
                                // ...
                            });
                        }
                    }),
                    Ox.MenuButton({
                        items: [
                            {id: '', title: Ox._('Library')}
                        ],
                        overlap: 'left',
                        title: 'list',
                        tooltip: Ox._('Download Book to a List'),
                        type: 'image'
                    })
                    .bindEvent({
                        click: function() {
                            // ...
                        }
                    })
                ],
                float: 'right'
            })
            : data.mediastate == 'transferring'
            ? Ox.FormElementGroup({
                elements: [
                    Ox.Button({
                        title: Ox._('Transferring...'),
                        width: 112
                    })
                    .bindEvent({
                        click: function() {
                            oml.UI.set({page: 'transfers'});
                        }
                    }),
                    Ox.Button({
                        overlap: 'left',
                        title: 'close',
                        tooltip: Ox._('Cancel Transfer'),
                        type: 'image'
                    })
                    .bindEvent({
                        click: function() {
                            data.mediastate = 'unavailable';
                            that.update(data, $data);
                            oml.api.cancelDownload({id: ui.item}, function() {
                                that.update(ui.item, $data);
                            });
                        }
                    })
                ],
                float: 'right'
            })
            : Ox.Button({
                title: Ox._('Read Book'),
                width: 128
            })
            .bindEvent({
                click: function() {
                    oml.UI.set({itemView: 'book'});
                }
            });
    }

    that.update = function(idOrData, $elements) {

        var data = Ox.isObject(idOrData) ? idOrData : null,
            id = data ? null : idOrData;

        $elements = $elements 
            ? Ox.makeArray($elements)
            : [$cover, $info, $data];

        (data ? Ox.noop : oml.api.get)({
            id: id,
            keys: []
        }, function(result) {

            if (result) {
                data = result.data;
            }
            Ox.print('BOOK DATA', data)

            var $reflection, $mediaButton,
                ratio = data.coverRatio || 0.75,
                size = 256,
                width = Math.round(ratio >= 1 ? size : size * ratio),
                height = Math.round(ratio <= 1 ? size : size / ratio),
                left = Math.floor((size - width) / 2),
                src = '/' + data.id + '/cover256.jpg',
                reflectionSize = Math.round(size / 2);

            $elements.forEach(function($element) {

                $element.empty();

                if ($element == $cover) {

                    $('<img>')
                        .attr({src: src})
                        .css({
                            position: 'absolute',
                            left: left + 'px',
                            width: width + 'px',
                            height: height + 'px'
                        })
                        .appendTo($cover);

                    $reflection = $('<div>')
                        .addClass('OxReflection')
                        .css({
                            position: 'absolute',
                            top: height + 'px',
                            width: size + 'px',
                            height: reflectionSize + 'px',
                            overflow: 'hidden'
                        })
                        .appendTo($cover);

                    $('<img>')
                        .attr({src: src})
                        .css({
                            position: 'absolute',
                            left: left + 'px',
                            width: width + 'px',
                            height: height + 'px'
                        })
                        .appendTo($reflection);

                    $('<div>')
                        .css({
                            position: 'absolute',
                            width: size + 'px',
                            height: reflectionSize + 'px'
                        })
                        .appendTo($reflection);

                } else if ($element == $info) {

                    $('<div>')
                        .css({
                            marginTop: '-4px',
                            fontSize: '13px',
                            fontWeight: 'bold'
                        })
                        .text(data.title || '')
                        .appendTo($info);

                    $('<div>')
                        .css({
                            marginTop: '4px',
                            fontSize: '13px',
                            fontWeight: 'bold'
                        })
                        .text((data.author || []).join(', '))
                        .appendTo($info);

                    $('<div>')
                        .css({
                            marginTop: '8px'
                        })
                        .text(
                            (data.place || '')
                            + (data.place && (data.publisher || data.date) ? ' : ' : '')
                            + (data.publisher || '')
                            + (data.publisher && data.date ? ', ' : '')
                            + (data.date || '')
                        )
                        .appendTo($info);

                    $('<div>')
                        .css({
                            marginTop: '8px',
                            textAlign: 'justify'
                        })
                        .html(
                            data.description
                            ? Ox.encodeHTMLEntities(data.description)
                            : '<span class="OxLight">No description</span>'
                        )
                        .appendTo($info);

                } else if ($element == $data) {

                    $mediaButton = renderMediaButton(data)
                        .appendTo($data);

                    $('<div>')
                        .addClass('OxSelectable')
                        .css({
                            marginTop: '8px',
                        })
                        .text(
                            [
                                data.extension.toUpperCase(),
                                Ox.formatValue(data.size, 'B')
                            ].join(', ')
                        )
                        .appendTo($data);

                    ['accessed', 'modified', 'added', 'created'].forEach(function(id) {
                        var title;
                        if (data[id]) {
                            title = Ox.getObjectById(oml.config.itemKeys, id).title;
                            $('<div>')
                                .css({
                                    marginTop: '8px',
                                    fontWeight: 'bold'
                                })
                                .text(title)
                                .appendTo($data);
                            Ox.EditableContent({
                                    editable: false,
                                    format: function(value) {
                                        return value ? Ox.formatDate(value, '%b %e, %Y') : '';
                                    },
                                    placeholder: Ox._('unknown'),
                                    value: data[id] || ''
                                })
                                .appendTo($data);
                        }
                    });

                    Ox.Button({
                            title: Ox._('Identify Book...'),
                            width: 128
                        })
                        .css({marginTop: '16px'})
                        .bindEvent({
                            click: function() {
                                identify(data);
                            }
                        })
                        .appendTo($data);

                    [
                        'isbn10', 'isbn13', 'lccn', 'olid', 'oclc', 'mainid'
                    ].forEach(function(id, index) {

                        var title = Ox.getObjectById(oml.config.itemKeys, id).title,
                            placeholder = id == 'mainid' ? 'none' : 'unknown';

                        $('<div>')
                            .css({
                                marginTop: (index == 0 ? 10 : 6) + 'px',
                                fontWeight: 'bold'
                            })
                            .text(title)
                            .appendTo($data);

                        Ox.EditableContent({
                                editable: true,
                                format: function(value) {
                                    return id == 'mainid'
                                        ? Ox.getObjectById(oml.config.itemKeys, value).title
                                        : value;
                                },
                                placeholder: placeholder,
                                tooltip: Ox._('Doubleclick to edit'),
                                value: data[id] || ''
                            })
                            .bindEvent({
                                submit: function(data) {
                                    editMetadata(id, data.value);
                                }
                            })
                            .appendTo($data);

                    });

                    $('<div>').css({height: '16px'}).appendTo($data);

                }

            });

            function editMetadata(key, value) {
                var edit;
                if (value != data[key]) {
                    edit = Ox.extend({id: ui.item}, key, value);
                    oml.api.edit(edit, function(result) {
                        that.update(result.data, $data);
                    });
                }
            }

        });

    };

    ui.item && that.update(ui.item);

    oml.bindEvent({
        transfer: function(data) {
            if (data.id == ui.item && data.progress == 1) {
                Ox.Request.clearCache(); // FIXME: too much
                that.update(ui.item, $data);
            }
        }
    });

    return that;

};
