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

    function formatLight(str) {
        return '<span class="OxLight">' + str + '</span>';
    }

    function formatValue(value, key) {
        return (Ox.isArray(value) ? value : [value]).map(function(value) {
            return key ?
                '<a href="/' + key + '==' + value + '">' + value + '</a>'
                : value;
        }).join(', ');
    }

    function identify(data) {
        oml.ui.identifyDialog(data).open();
        return;
        $identifyPanel.select('id');
        $identifyDialog.open();
        identify(data);
        function identify(data) {
            oml.api.identify(data, function(result) {
                $identifyList.options({
                    items: result.data.items.map(function(item, index) {
                        return Ox.extend(item, {index: index});
                    })
                });
            });
        }
    }

    function renderMediaButton(data) {
        function getListItems() {
            var items = [];
            if (ui._lists) {
                items = ui._lists.filter(function(list) {
                    return list.user == oml.user.preferences.username
                        && list.type != 'smart';
                }).map(function(list) {
                    return {
                        id: list.id,
                        title: Ox._('Download to {0}', [list.name])
                    };
                });
                items.splice(1, 0, [{}]);
            }
            return items;
        }
        function setListItems() {
            if ($element && ui._lists) {
                $element.options({
                    disabled: false
                }).options('elements')[1].options({
                    items: getListItems()
                });
            } else {
                setTimeout(setListItems, 100);
            }
        }
        
        if (data.mediastate == 'unavailable' && !ui._lists) {
            setListItems();
        }
        var $element = data.mediastate == 'unavailable'
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
                        disabled: !ui._lists,
                        items: getListItems(),
                        overlap: 'left',
                        title: 'list',
                        tooltip: Ox._('Download Book to a List'),
                        type: 'image'
                    })
                    .bindEvent({
                        click: function(data) {
                            data.mediastate = 'transferring';
                            that.update(data, $data);
                            oml.api.download(Ox.extend({
                                id: ui.item,
                            }, data.id == ':' ? {} : {
                                list: data.id.slice(1)
                            }), function(result) {
                                // ...
                            });
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
        return $element;
    }

    that.update = function(idOrData, $elements) {

        var data = Ox.isObject(idOrData) ? idOrData : null,
            id = data ? null : idOrData,

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
                isEditable = !data.mainid && data.mediastate == 'available',
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
                        .css({marginTop: '-2px'})
                        .append(
                            Ox.EditableContent({
                                clickLink: oml.clickLink,
                                editable: isEditable,
                                tooltip: isEditable ? oml.getEditTooltip() : '',
                                value: data.title
                            })
                            .css({
                                fontSize: '13px',
                                fontWeight: 'bold'
                            })
                        )
                        .appendTo($info);

                    if (data.author || isEditable) {
                        $('<div>')
                            .css({
                                marginTop: '4px',
                                fontSize: '13px',
                                fontWeight: 'bold'
                            })
                            .append(
                                Ox.EditableContent({
                                    clickLink: oml.clickLink,
                                    editable: isEditable,
                                    format: function(value) {
                                        return formatValue(value.split(', '), 'author');
                                    },
                                    placeholder: formatLight(Ox._('Unknown Author')),
                                    tooltip: isEditable ? oml.getEditTooltip() : '',
                                    value: data.author ? data.author.join(', ') : ''
                                })
                                .css({
                                    fontSize: '13px',
                                    fontWeight: 'bold'
                                })
                            )
                            .appendTo($info);
                    }


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

                    if (data.description) {
                        $('<div>')
                            .css({
                                marginTop: '8px',
                                textAlign: 'justify'
                            })
                            .html(Ox.encodeHTMLEntities(data.description))
                            .appendTo($info);
                    }


                } else if ($element == $data) {

                    $mediaButton = renderMediaButton(data)
                        .appendTo($data);

                    $('<div>')
                        .addClass('OxSelectable')
                        .css({
                            marginTop: '10px',
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
                            $('<div>')
                                .text(Ox.formatDate(data[id], '%b %e, %Y'))
                                .appendTo($data);
                        }
                    });

                    Ox.Button({
                            disabled: data.mediastate != 'available',
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
                        'isbn10', 'isbn13', 'asin', 'lccn', 'oclc', 'olid'
                    ].forEach(function(id, index) {
                        var title;
                        if (data[id]) {
                            title = Ox.getObjectById(oml.config.itemKeys, id).title;
                            $('<div>')
                                .css({
                                    marginTop: (index == 0 ? 10 : 6) + 'px',
                                    fontWeight: 'bold'
                                })
                                .text(title)
                                .appendTo($data);
                            Ox.EditableContent({
                                    editable: false,
                                    value: data[id]
                                })
                                .appendTo($data);
                        }
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
