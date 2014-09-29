'use strict';

oml.ui.infoView = function(identifyData) {

    var ui = oml.user.ui,

        iconSize = identifyData ? 256 : ui.iconSize,

        css = getCSS(iconSize, oml.config.iconRatio),

        ids = [
            {key: 'isbn', url: 'https://google.com/search?q=ISBN+{0}'},
            {key: 'asin', url: 'http://www.amazon.com/dp/{0}'},
            {key: 'lccn', url: 'http://lccn.loc.gov/{0}'},
            {key: 'oclc', url: 'https://www.worldcat.org/oclc/{0}'},
            {key: 'olid', url: 'https://openlibrary.org/books/{0}'}
        ],

        that = Ox.Element()
            .addClass('OxTextPage')
            .css({overflowY: 'auto'})
            .bindEvent({
                oml_icons: function() {
                    that.updateElement(ui.item, [$icon])
                },
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

        $icon = Ox.Element()
            .css({
                position: 'absolute',
                left: '16px',
                top: '16px',
                width: css.icon.width
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
            [iconSize == 512 ? 'hide' : 'show']()
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
            icon: {
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

    function getIconTooltip() {
        return !identifyData
            ? 'Click to see ' + (ui.iconSize == 256 ? 'large' : 'small')
                + ' ' + ui.icons + ', doubleclick to see '
                + (ui.icons == 'cover' ? 'preview' : 'cover')
            : '';
    }

    function formatLight(string) {
        return '<span class="OxLight">' + string + '</span>';
    }

    function formatKey(key) {
        var item = Ox.getObjectById(oml.config.itemKeys, key);
        return '<span style="font-weight: bold">'
            + Ox._(Ox.toTitleCase(key)) + ':</span>&nbsp;';
    }

    function formatValue(value, key) {
        return value ? (Ox.isArray(value) ? value : [value]).map(function(value) {
            return key && !identifyData ?
                '<a href="/' + key + '==' + (
                    key == 'date' ? value.slice(0, 4) : value
                ) + '">' + value + '</a>'
                : value;
        }).join('; ') : '';
    }

    function identify(data) {
        oml.$ui.identifyDialog = oml.ui.identifyDialog(data).open();
    }

    function renderIdentifyButton(data) {
        return Ox.FormElementGroup({
            elements: [
                Ox.Button({
                    disabled: data.mediastate != 'available',
                    title: Ox._('Identify Book...'),
                    width: 112
                })
                .bindEvent({
                    click: function() {
                        identify(data);
                    }
                }),
                data.mediastate == 'available' && data.primaryid
                    ? Ox.Select({
                        items: Ox.flatten(ids.map(function(id) {
                            return (data[id.key] || []).map(function(value) {
                                return {
                                    id: id.key + ':' + value,
                                    title: '<b>' + Ox.getObjectById(
                                        oml.config.itemKeys, id.key
                                    ).title + ':</b> ' + value
                                };
                            });
                        })).concat([
                            {id: '', title: '<b>No ID</b>'}
                        ]),
                        max: 1,
                        min: 1,
                        overlap: 'left',
                        title: 'select',
                        tooltip: Ox._('Set Primary ID'),
                        type: 'image',
                        value: data.primaryid.join(':')
                    })
                    .bindEvent({
                        click: function(data) {
                            // ...
                        },
                        change: function(data) {
                            oml.api.edit({
                                id: ui.item,
                                primaryid: data.value ? data.value.split(':') : ''
                            }, function(result) {
                                that.updateElement(result.data, [$data]);
                            });
                        }
                    })
                : Ox.Button({
                    disabled: true,
                    overlap: 'left',
                    title: 'select',
                    type: 'image'
                })
            ],
            float: 'right'
        })
        .css({marginTop: '16px'});
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
                        title: 'select',
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
                            oml.api.cancelDownloads({ids: [ui.item]}, function() {
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
        iconSize = iconSize == 256 ? 512 : 256,
        css = getCSS(iconSize, ratio);
        //$icon.animate(css.icon, 250);
        $info.animate(css.info, 250);
        $image.animate(css.image, 250);
        $reflectionImage.animate(css.image, 250);
        $reflection.animate(css.reflection, 250);
        oml.UI.set({iconSize: iconSize});
    }

    function updateCover(ratio) {
        var css = getCSS(iconSize, ratio);
        $image.css(css.image).show();
        $reflectionImage.css(css.image);
        $reflection.css(css.reflection).show();
    }

    that.updateElement = function(idOrData, $elements) {

        var data = Ox.isObject(idOrData) ? idOrData : null,
            id = data ? null : idOrData,

        $elements = $elements 
            ? Ox.makeArray($elements)
            : [$icon, $info, $data];

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

            Ox.print('BOOK DATA', data)

            var $div,
                isEditable = data.mediastate == 'available' && !identifyData,
                src = !identifyData
                    ? '/' + data.id + '/' + ui.icons + '512.jpg?' + data.modified
                    : data.cover,
                ratio = (
                    ui.icons == 'cover' || identifyData
                    ? data.coverRatio : data.previewRatio
                ) || oml.config.iconRatio,
                size = iconSize,
                reflectionSize = Math.round(size / 2);

            $elements.forEach(function($element) {

                $element.empty();

                if ($element == $icon) {

                    $image = Ox.Element({
                            element: '<img>',
                            tooltip: getIconTooltip()
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
                            doubleclick: function() {
                                if (!identifyData) {
                                    oml.UI.set({
                                        icons: ui.icons == 'cover'
                                            ? 'preview' : 'cover'
                                    });
                                }
                            },
                            singleclick: function() {
                                if (!identifyData) {
                                    toggleCoverSize(ratio);
                                }
                            }
                        })
                        .appendTo($icon);

                    $reflection = $('<div>')
                        .addClass('OxReflection')
                        .css({
                            position: 'absolute',
                            width: size + 'px',
                            height: reflectionSize + 'px',
                            overflow: 'hidden'
                        })
                        .hide()
                        .appendTo($icon);

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

                    // -------- Title

                    $('<div>')
                        .css({
                            marginTop: '-2px'
                        })
                        .append(
                            Ox.EditableContent({
                                    clickLink: oml.clickLink,
                                    editable: isEditable,
                                    tooltip: isEditable ? oml.getEditTooltip() : '',
                                    value: data.title || 'No Title'
                                })
                                .css({
                                    fontWeight: 'bold',
                                    fontSize: '13px'
                                })
                                .bindEvent({
                                    submit: function(event) {
                                        editMetadata('title', event.value);
                                    }
                                })
                        )
                        .appendTo($info);

                    // -------- Author

                    $('<div>')
                        .css({
                            marginTop: '2px'
                        })
                        .append(
                            Ox.EditableContent({
                                    clickLink: oml.clickLink,
                                    editable: isEditable,
                                    format: function(value) {
                                        return formatValue(value.split('; '), 'author');
                                    },
                                    placeholder: formatLight(Ox._('Unknown Author')),
                                    tooltip: isEditable ? oml.getEditTooltip() : '',
                                    value: data.author ? data.author.join('; ') : ''
                                })
                                .css({
                                    marginBottom: '-3px',
                                    fontWeight: 'bold',
                                    fontSize: '13px'
                                })
                                .bindEvent({
                                    submit: function(event) {
                                        editMetadata('author', event.value);
                                    }
                                })
                        )
                        .appendTo($info);

                    // -------- Place, Publisher, Date

                    $div = $('<div>')
                        .css({
                            marginTop: '4px',
                        })
                        .appendTo($info);
                    ['place', 'publisher', 'date'].forEach(function(key, index) {
                        if (index) {
                            $('<span>').html(', ').appendTo($div);
                        }
                        $('<span>')
                            .html(formatKey(key))
                            .appendTo($div);
                        Ox.EditableContent({
                                clickLink: oml.clickLink,
                                editable: isEditable,
                                format: function(value) {
                                    return formatValue(value.split('; '), key)
                                },
                                placeholder: formatLight('unknown'),
                                tooltip: isEditable ? oml.getEditTooltip() : '',
                                value: key == 'place'
                                    ? (data[key] ? data[key].join('; ') : [''])
                                    : data[key] || ''
                            })
                            .bindEvent({
                                submit: function(event) {
                                    editMetadata(key, event.value);
                                }
                            })
                            .appendTo($div);
                    });

                    // -------- Edition, Language, Pages

                    $div = $('<div>')
                        .css({
                            marginTop: '4px',
                        })
                        .appendTo($info);
                    ['edition', 'language', 'pages'].forEach(function(key, index) {
                        if (index) {
                            $('<span>').html(', ').appendTo($div);
                        }
                        $('<span>')
                            .html(formatKey(key))
                            .appendTo($div);
                        Ox.EditableContent({
                                clickLink: oml.clickLink,
                                editable: isEditable,
                                format: function(value) {
                                    return key == 'language'
                                        ? formatValue(value, key)
                                        : value;
                                },
                                placeholder: formatLight('unknown'),
                                tooltip: isEditable ? oml.getEditTooltip() : '',
                                value: data[key] || ''
                            })
                            .bindEvent({
                                submit: function(event) {
                                    editMetadata(key, event.value);
                                }
                            })
                            .appendTo($div);
                    });

                    // -------- Primary ID

                    if (data.primaryid) {
                        $('<div>')
                            .css({
                                marginTop: '4px',
                            })
                            .html(
                                '<b>' + Ox.getObjectById(oml.config.itemKeys, data.primaryid[0]).title
                                + ':</b> ' + data.primaryid[1]
                            )
                            .appendTo($info);
                    }

                    // -------- Classification

                    if (data.classification) {
                        $('<div>')
                            .css({
                                marginTop: '8px',
                            })
                            .html(
                                formatValue(data.classification, 'classification')
                            )
                            .appendTo($info);
                    }

                    // -------- Description

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

                    oml.createLinks($info);

                } else if ($element == $data) {

                    renderMediaButton(data).appendTo($data);

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

                    renderIdentifyButton(data).appendTo($data);

                    ids.forEach(function(id, index) {
                        var title;
                        if (data[id.key] && !Ox.isEmpty(data[id.key])) {
                            title = Ox.getObjectById(oml.config.itemKeys, id.key).title;
                            $('<div>')
                                .css({
                                    marginTop: (index == 0 ? 10 : 6) + 'px',
                                    fontWeight: 'bold'
                                })
                                .text(title)
                                .appendTo($data);
                            Ox.makeArray(data[id.key]/*FIXME!*/).forEach(function(value) {
                                var isPrimary = data.primaryid[0] == id.key
                                    && data.primaryid[1] == value;
                                value = Ox.encodeHTMLEntities(value);
                                Ox.Element({
                                        tooltip: isPrimary ? 'Primary ID' : ''
                                    })
                                    .html(
                                        '<a href="' + Ox.formatString(id.url, [value])
                                        + '" target="_blank">' + value + '</a>'
                                        + (isPrimary ? ' (*)' : '')
                                    )
                                    .appendTo($data);
                            });
                        }
                    });

                    $('<div>').css({height: '16px'}).appendTo($data);

                }

            });

            function editMetadata(key, value) {
                if (value != data[key]) {
                    var edit = {id: data.id};
                    if (Ox.contains(['author', 'place'], key)) {
                        edit[key] = value ? value.split('; ') : [];
                    } else {
                        edit[key] = value;
                    }
                    oml.api.edit(edit, function(result) {
                        oml.$ui.browser.value(
                            result.data.id, key, result.data[key]
                        );
                    });
                }
            }

        });

    };

    if (!identifyData) {
        ui.item && that.updateElement(ui.item);
    } else {
        that.updateElement(identifyData, [$icon, $info]);
    }

    oml.bindEvent({
        transfer: function(data) {
            if (data.id == ui.item && data.progress == 1) {
                Ox.Request.clearCache(); // FIXME: too much
                that.updateElement(ui.item, [$info, $data]);
            }
        }
    });
    that.bindEvent({
        mousedown: function() {
            that.gainFocus();
        }
    })

    return that;

};
