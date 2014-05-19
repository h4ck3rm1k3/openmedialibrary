'use strict';

oml.ui.infoView = function(identifyData) {

    var ui = oml.user.ui,

        coverSize = identifyData ? 256 : ui.coverSize,

        css = getCSS(coverSize, oml.config.coverRatio),

        that = Ox.Element()
            .addClass('OxTextPage')
            .css({overflowY: 'auto'})
            .bindEvent({
                oml_item: function() {
                    if (ui.item) {
                        that.updateElement(ui.item);
                    }
                },
                oml_listselection: function(data) {
                    if (data.value && data.value.length) {
                        that.updateElement(data.value[0]);
                    }
                }
            }),

        $cover = Ox.Element()
            .css({
                position: 'absolute',
                left: '16px',
                top: '16px',
                width: css.cover.width
            })
            .appendTo(that),

        $info = Ox.Element()
            .addClass('OxSelectable')
            .css({
                position: 'absolute',
                left: css.info.left,
                right: !identifyData ? '176px' : 16 + Ox.UI.SCROLLBAR_SIZE + 'px',
                top: '16px'
            })
            [coverSize == 512 ? 'hide' : 'show']()
            .appendTo(that),

        $data,

        $image, $reflection, $reflectionImage;

    if (!identifyData) {
        $data = Ox.Element()
            .addClass('OxSelectable')
            .css({
                position: 'absolute',
                right: '16px',
                top: '16px',
                width: '128px'
            })
            .appendTo(that);
    }

    function getCSS(size, ratio) {
        var width = Math.round(ratio >= 1 ? size : size * ratio),
            height = Math.round(ratio <= 1 ? size : size / ratio),
            left = size == 256 ? Math.floor((size - width) / 2) : 0;
        return {
            cover: {
                width: size + 'px'
            },
            info: {
                left: (size == 256 ? size + 32 : width + 48) + 'px'
            },
            image: {
                left: left + 'px',
                width: width + 'px',
                height: height + 'px'
            },
            reflection: {
                top: height + 'px'
            }
        };
    }

    function getImageSize(size, ratio) {
        var width = Math.round(ratio >= 1 ? size : size * ratio),
            height = Math.round(ratio <= 1 ? size : size / ratio),
            left = Math.floor((size - width) / 2);
        return {width: width, height: height, left: left};
    }

    function formatLight(str) {
        return '<span class="OxLight">' + str + '</span>';
    }

    function formatKey(key) {
        var item = Ox.getObjectById(oml.config.itemKeys, key);
        return '<span style="font-weight: bold">'
            + Ox._(Ox.toTitleCase(key)) + ':&nbsp;</span> ';
    }

    function formatValue(value, key, join) {
        value = Ox.encodeHTMLEntities(value);
        return value ? (Ox.isArray(value) ? value : [value]).map(function(value) {
            return key ?
                '<a href="/' + key + '==' + value + '">' + value + '</a>'
                : value;
        }).join(join || ', ') : '';
    }

    function identify(data) {
        oml.ui.identifyDialog(data).open();
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
                            that.updateElement(data, $data);
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
                            that.updateElement(data, $data);
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
                            that.updateElement(data, $data);
                            oml.api.cancelDownload({id: ui.item}, function() {
                                that.updateElement(ui.item, $data);
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

    function toggleCoverSize(ratio) {
        var css;
        coverSize = coverSize == 256 ? 512 : 256,
        css = getCSS(coverSize, ratio);
        //$cover.animate(css.cover, 250);
        $info.animate(css.info, 250);
        $image.animate(css.image, 250);
        $reflectionImage.animate(css.image, 250);
        $reflection.animate(css.reflection, 250);
        oml.UI.set({coverSize: coverSize});
    }

    function updateCover(ratio) {
        var css = getCSS(coverSize, ratio);
        $image.css(css.image).show();
        $reflectionImage.css(css.image);
        $reflection.css(css.reflection).show();
    }

    that.updateElement = function(idOrData, $elements) {

        var data = Ox.isObject(idOrData) ? idOrData : null,
            id = data ? null : idOrData,

        $elements = $elements 
            ? Ox.makeArray($elements)
            : [$cover, $info, $data];

        (data ? Ox.noop : oml.api.get)({
            id: id,
            keys: []
        }, function(result) {

            if (!identifyData && id && id != ui.item) {
                return;
            }

            if (result) {
                data = result.data;
            }

            var $mediaButton,
                isEditable = !data.mainid && data.mediastate == 'available',
                src = !identifyData
                    ? '/' + data.id + '/cover512.jpg?' + data.modified
                    : data.cover,
                ratio = data.coverRatio || oml.config.coverRatio,
                size = coverSize,
                reflectionSize = Math.round(size / 2);

            $elements.forEach(function($element) {

                $element.empty();

                if ($element == $cover) {

                    $image = Ox.Element({
                            element: '<img>',
                            tooltip: '' // TODO
                        })
                        .on({
                            error: function() {
                                if (size == 512) {
                                    $info.show();
                                }
                            },
                            load: function() {
                                ratio = $image[0].width / $image[0].height;
                                updateCover(ratio);
                                if (size == 512) {
                                    $info.css({
                                        left: getCSS(512, ratio).info.left
                                    }).show();
                                }
                            }
                        })
                        .attr({src: src})
                        .css({
                            position: 'absolute'
                        })
                        .hide()
                        .bindEvent({
                            singleclick: function() {
                                if (!identifyData) {
                                    toggleCoverSize(ratio);
                                }
                            }
                        })
                        .appendTo($cover);

                    $reflection = $('<div>')
                        .addClass('OxReflection')
                        .css({
                            position: 'absolute',
                            width: size + 'px',
                            height: reflectionSize + 'px',
                            overflow: 'hidden'
                        })
                        .hide()
                        .appendTo($cover);

                    $reflectionImage = $('<img>')
                        .attr({src: src})
                        .css({
                            position: 'absolute'
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
                            marginTop: '-2px',
                            fontSize: '13px',
                            fontWeight: 'bold'
                        })
                        .html(
                            data.title ? Ox.encodeHTMLEntities(data.title)
                            : '<span class="OxLight">'
                                + Ox._('No Title')
                                + '</span>'
                        )
                        .appendTo($info);

                    if (data.author) {
                        $('<div>')
                            .css({
                                marginTop: '4px',
                                fontSize: '13px',
                                fontWeight: 'bold'
                            })
                            .html(formatValue(data.author, 'author'))
                            .appendTo($info);
                    }

                    if (data.place || data.publisher || data.date) {
                        $('<div>')
                            .css({
                                marginTop: '8px'
                            })
                            .html(
                                (formatValue(data.place, 'place', ' ; '))
                                + (data.place && (data.publisher || data.date) ? ' : ' : '')
                                + (formatValue(data.publisher, 'publisher'))
                                + (data.publisher && data.date ? ', ' : '')
                                + (data.date || '')
                            )
                            .appendTo($info);
                    }

                    if (data.edition || data.language) {
                        $('<div>')
                            .css({
                                marginTop: '8px'
                            })
                            .html(
                                (Ox.encodeHTMLEntities(data.edition || ''))
                                + (data.edition && data.language ? '; ' : '')
                                + (formatValue(data.language, 'language'))
                            )
                            .appendTo($info);
                    }

                    if (data.classification) {
                        $('<div>')
                            .css({
                                marginTop: '8px',
                                textAlign: 'justify'
                            })
                            .html(
                                Ox.formatValue(data.classification, 'classification')
                            )
                            .appendTo($info);
                    }

                    if (data.description) {
                        $('<div>')
                            .css({
                                marginTop: '8px',
                                textAlign: 'justify'
                            })
                            .html(
                                Ox.encodeHTMLEntities(data.description)
                            )
                            .appendTo($info);
                    }

                    $('<div>').css({height: '16px'}).appendTo($info);

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

            // FIXME: identify dialog should call this too
            function editMetadata(key, value) {
                var edit;
                Ox.print('EM', key, value, data[key])
                if (value != data[key]) {
                    edit = Ox.extend({id: ui.item}, key, value);
                    oml.api.edit(edit, function(result) {
                        Ox.Request.clearCache('find');
                        oml.$ui.browser.reloadList();
                        //that.updateElement(result.data, $info);
                    });
                }
            }

        });

    };

    if (!identifyData) {
        ui.item && that.updateElement(ui.item);
    } else {
        that.updateElement(identifyData, [$cover, $info]);
    }

    oml.bindEvent({
        transfer: function(data) {
            if (data.id == ui.item && data.progress == 1) {
                Ox.Request.clearCache(); // FIXME: too much
                that.updateElement(ui.item, [$info, $data]);
            }
        }
    });

    return that;

};
