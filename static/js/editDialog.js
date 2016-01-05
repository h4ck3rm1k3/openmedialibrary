'use strict';

oml.ui.editDialog = function() {

    var arrayKeys = [
            'author', 'place', 'publisher', 'language'
        ],
        ids = oml.user.ui.listSelection,
        keys = [
            'title', 'author', 'place', 'publisher', 'date',
            'edition', 'language', 'pages', 'description'
        ],
        mixed = ' ',
        separator = '; ',
        tooltip = Ox._('Doubleclick to edit'),

        $info = Ox.Element()
            .addClass('OxSelectable')
            .css({padding: '16px'});

    var that = Ox.Dialog({
            buttons: [
                Ox.Button({
                    title: Ox._('Done')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                    }
                })
            ],
            closeButton: true,
            content: Ox.LoadingScreen().start(),
            height: 256,
            removeOnClose: true,
            title: Ox._('Edit Metadata for {0}', [
                Ox.formatNumber(ids.length) + ' ' + (
                    ids.length == 1 ? 'Book' : 'Books'
                )
            ]),
            width: 512
        });

    getMetadata(renderMetadata);

    function editMetadata(key, value) {
        var edit = {id: ids};
        if (Ox.contains(['author', 'place'], key)) {
            edit[key] = value ? value.split(separator) : [];
        } else {
            edit[key] = value;
        }
        oml.api.edit(edit, function(result) {
            Ox.Request.clearCache();
            oml.$ui.filters.forEach(function($filter) {
                $filter.reloadList();
            });
            oml.$ui.list.reloadList();
        });
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
        var isMixed = value === mixed || (
            Ox.isArray(value) && value.length == 1 && value[0] === mixed
        );
        return isMixed ? formatLight(Ox._(
            key == 'title' ? 'Mixed Title'
                : key == 'author' ? 'Mixed Author'
                : key == 'description' ? 'Mixed Description'
                : 'mixed'
        )) : value ? (Ox.isArray(value) ? value : [value]).map(function(value) {
            return key == 'date' && value ? value.slice(0, 4) : value;
        }).join(separator) : '';
    }

    function getMetadata(callback) {
        oml.api.find({
            keys: keys,
            query: {
                conditions: ids.map(function(id) {
                    return {
                        key: 'id',
                        operator: '==',
                        value: id
                    };
                }),
                operator: '|'
            }
        }, function(result) {
            var data = {},
                items = result.data.items;
            keys.forEach(function(key) {
                var values = items.map(function(item) {
                    return item[key];
                });
                var isArray = Ox.isArray(values[0])
                if (isArray) {
                    values = values.map(function(value) {
                        return value.join(separator);
                    });
                }
                data[key] = Ox.unique(values).length == 1
                    ? (isArray ? values[0].split(separator) : values[0])
                    : isArray ? [mixed] : mixed;
            });
            callback(data);
        });
    }

    function renderMetadata(data) {

        var $div;

        // Title

        $('<div>')
            .css({
                marginTop: '-2px'
            })
            .append(
                Ox.EditableContent({
                    editable: true,
                    format: function(value) {
                        return formatValue(value, 'title');
                    },
                    placeholder: formatLight(Ox._('No Title')),
                    tooltip: tooltip,
                    value: data.title || ''
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

        // Author

        $('<div>')
            .css({
                marginTop: '2px'
            })
            .append(
                Ox.EditableContent({
                    editable: true,
                    format: function(value) {
                        return formatValue(value.split(separator), 'author');
                    },
                    placeholder: formatLight(Ox._('Unknown Author')),
                    tooltip: tooltip,
                    value: data.author ? data.author.join(separator) : ''
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

        // Place, Publisher, Date

        $div = $('<div>')
            .css({
                marginTop: '4px'
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
                    editable: true,
                    format: function(value) {
                        return formatValue(
                            key == 'place' ? value.split(separator) : value,
                            key
                        );
                    },
                    placeholder: formatLight(Ox._('unknown')),
                    tooltip: tooltip,
                    value: data[key] ? (
                        Ox.contains(arrayKeys, key) && Ox.isArray(data[key])
                        ? data[key].join('; ') : data[key]
                    ) : ''
                })
                .bindEvent({
                    submit: function(event) {
                        editMetadata(key, event.value);
                    }
                })
                .appendTo($div);
        });

        // Edition, Language, Pages

        $div = $('<div>')
            .css({
                marginTop: '4px'
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
                    editable: true,
                    format: function(value) {
                        return formatValue(
                            key == 'language' ? value.split(separator) : value,
                            key
                        );
                    },
                    placeholder: formatLight(Ox._('unknown')),
                    tooltip: tooltip,
                    value: data[key] ? (
                        Ox.contains(arrayKeys, key) && Ox.isArray(data[key])
                        ? data[key].join(separator) : data[key]
                    ) : ''
                })
                .bindEvent({
                    submit: function(event) {
                        editMetadata(key, event.value);
                    }
                })
                .appendTo($div);
        });

        // Description

        $('<div>')
            .css({
                marginTop: '8px',
                textAlign: 'justify'
            }).append(
                Ox.EditableContent({
                        editable: true,
                        format: function(value) {
                            return formatValue(
                                Ox.encodeHTMLEntities(value), 'description'
                            );
                        },
                        placeholder: formatLight('No Description'),
                        tooltip: tooltip,
                        type: 'textarea',
                        value: data.description || ''
                    })
                    .bindEvent({
                        submit: function(event) {
                            editMetadata('description', event.value);
                        }
                    })
            ).appendTo($info);

        $('<div>').css({height: '16px'}).appendTo($info);

        that.options({content: $info});

    }

    return that;

};
