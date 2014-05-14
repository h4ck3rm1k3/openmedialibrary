'use strict';

oml.ui.identifyDialog = function(data) {

    var ui = oml.user.ui,

        ids = [
            'isbn10', 'isbn13', 'asin', 'lccn', 'oclc', 'olid'
        ].map(function(id) {
            return {
                id: id,
                title: Ox.getObjectById(oml.config.itemKeys, id).title
            };
        }),

        keys = [
            'title', 'author', 'publisher', 'date'
        ].map(function(id) {
            var key = Ox.getObjectById(oml.config.sortKeys, id);
            return {
                format: key.format,
                id: id,
                operator: key.operator,
                width: {
                    title: 288,
                    author: 224,
                    publisher: 160,
                    date: 96 - Ox.UI.SCROLLBAR_SIZE
                }[id],
                title: key.title,
                visible: true
            };
        }),

        originalData = Ox.clone(data, true),

        $idForm = renderIdForm(data),

        $preview = data.mainid
            ? oml.ui.infoView(data)
            : Ox.Element(),

        $idPanel = Ox.SplitPanel({
            elements: [
                {element: Ox.Element().append($idForm), size: 96},
                {element: $preview}
            ],
            orientation: 'vertical'
        }),

        $titleForm = Ox.Element(),

        $inputs = keys.map(function(key, index) {
            return Ox.Input({
                    label: Ox._(key.title),
                    labelWidth: 64,
                    value: data[key.id],
                    width: 360
                })
                .css({
                    position: 'absolute',
                    left: index < 2 ? '16px' : '392px',
                    top: index % 2 == 0 ? '16px' : '40px'
                })
                .bindEvent({
                    submit: function(data) {
                        $findButton.triggerEvent('click');
                    }
                })
                .appendTo($titleForm);
        }),

        $clearButton = Ox.Button({
                title: Ox._('Clear'),
                width: 64
            })
            .css({
                position: 'absolute',
                right: '160px',
                top: '64px'
            })
            .bindEvent({
                click: function() {
                    keys.forEach(function(key) {
                        inputValue(key.id, '');
                    });
                    updateButtons();
                }
            })
            .appendTo($titleForm),

        $resetButton = Ox.Button({
                disabled: true,
                title: Ox._('Reset'),
                width: 64
            })
            .css({
                position: 'absolute',
                right: '88px',
                top: '64px'
            })
            .bindEvent({
                click: function() {
                    keys.forEach(function(key) {
                        inputValue(key.id, originalData[key.id]);
                    });
                    updateButtons();
                }
            })
            .appendTo($titleForm),

        $findButton = Ox.Button({
                title: Ox._('Find'),
                width: 64
            })
            .css({
                position: 'absolute',
                right: '16px',
                top: '64px'
            })
            .bindEvent({
                click: function() {
                    var data = {};
                    keys.forEach(function(key) {
                        data[key.id] = inputValue(key.id);
                    });
                    findMetadata(data);
                }
            })
            .appendTo($titleForm),

        $titlePanel = Ox.SplitPanel({
            elements: [
                {element: $titleForm, size: 96},
                {element: renderResults([Ox.extend({index: '0'}, data)])}
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

    function findMetadata(data) {
        $titlePanel.replaceElement(1, Ox.LoadingScreen().start());
        oml.api.findMetadata(data, function(result) {
            Ox.print('GOT RESULTS', result.data);
            var items = result.data.items.map(function(item, index) {
                    return Ox.extend({index: index.toString()}, item);
                }).concat([
                    Ox.extend({index: result.data.items.length.toString()}, data)
                ]);
            $titlePanel.replaceElement(1, renderResults(items));
        });
    }

    function getMetadata(key, value) {
        $idPanel.replaceElement(1, Ox.LoadingScreen().start());
        oml.api.getMetadata(Ox.extend({}, key, value), function(result) {
            Ox.print('GOT RESULT', result.data);
            $idForm = renderIdForm(result.data);
            $preview = oml.ui.infoView(result.data);
            $idPanel
                .replaceElement(0, $idForm)
                .replaceElement(1, $preview);
        });
    }

    function inputValue(key, value) {
        // FIXME: UNELEGANT
        Ox.print('INPUTVALUE', key, value)
        var $input =  $inputs[[
                'title', 'author', 'publisher', 'date'
            ].indexOf(key)];
        if (Ox.isUndefined(value)) {
            value = $input.value();
            if (key == 'author') {
                value = value ? value.split(', ') : [];
            }
        } else {
            $input.value(
                key == 'author' ? (value || []).join(', ') : value
            );
        }
        return value;
    }

    function isEmpty(data) {
        return Ox.every(data, Ox.isEmpty);
    }

    function isOriginal(data) {
        return Ox.every(data, function(value, key) {
            return value == originalData[key];
        });
    }

    function renderIdForm(data) {
        var $element = Ox.Element(),
            $elements = ids.map(function(id, index) {
                return Ox.FormElementGroup({
                    elements: [
                        Ox.Checkbox({
                            overlap: 'right',
                            title: Ox._(id.title),
                            value: id.id == data.mainid,
                            width: 80
                        })
                        .bindEvent({
                            change: function(data) {
                                var value = $elements[index].options('elements')[1].value()
                                if (data.value) {
                                    if (value) {
                                        $elements.forEach(function($element, i) {
                                            if (i != index) {
                                                $elements[i].options('elements')[0].value(false);
                                            }
                                        });
                                        getMetadata(id.id, value, function() {
                                            // ...
                                        });
                                    } else {
                                        this.value(false);
                                    }
                                } else {
                                    this.value(true);
                                }
                            }
                        }),
                        Ox.Input({
                            value: data[id.id] || '',
                            width: 160
                        })
                        .bindEvent({
                            submit: function(data) {
                                if (data.value) {
                                    $elements.forEach(function($element, i) {
                                        $element.options('elements')[0].options({
                                            disabled: true,
                                            value: i == index
                                        });
                                        $element.options('elements')[1].options({
                                            disabled: true
                                        });
                                    });
                                    getMetadata(id.id, data.value, function() {
                                        // ...
                                    });
                                }
                            }
                        })
                    ],
                    float: 'left'
                })
                .css({
                    position: 'absolute',
                    left: 16 + Math.floor(index / 2) * 248 + 'px',
                    top: 16 + (index % 2) * 24 + 'px'
                })
                .appendTo($element);
            }),
            $resetButton = Ox.Button({
                    disabled: true,
                    title: Ox._('Reset'),
                    width: 64
                })
                .css({
                    position: 'absolute',
                    right: '16px',
                    top: '64px'
                })
                .bindEvent({
                    click: function() {
                        /*
                        keys.forEach(function(key) {
                            inputValue(key.id, originalData[key.id]);
                        });
                        updateButtons();
                        */
                    }
                })
                .appendTo($element);
        return $element;
        Ox.print('???', data.mainid)
        return Ox.Form({
                items: Ox.flatten(ids.map(function(id) {
                    return [
                        Ox.Checkbox({
                                disabled: !data[id.id] || id.id == data.mainid,
                                id: id.id + 'Checkbox',
                                title: Ox._(id.title),
                                value: id.id == data.mainid,
                                width: 128
                            })
                            .bindEvent({
                                change: function() {
                                    getMetadata(id.id, data[id.id]);
                                }
                            }),
                        Ox.Input({
                                id: id.id + 'Input',
                                value: data[id.id] || '',
                                width: 128
                            })
                            .css({marginBottom: '16px'})
                            .bindEvent({
                                change: function(data) {
                                    if (data.value) {
                                        getMetadata(id.id, data.value, function() {
                                            //...
                                        });
                                    } else {
                                        Ox.print('this', this)
                                    }
                                }
                            })
                    ];
                }))
            })
            .css({margin: '16px'});
        return $form;
    }

    function renderResults(items) {
        Ox.print('LIST ITEMS::::', items);
        var $list = Ox.TableList({
                columns: Ox.clone(keys, true),
                items: items,
                min: 1,
                max: 1,
                scrollbarVisible: true,
                selected: ['0'],
                sort: [{key: 'index', operator: '+'}],
                unique: 'index'
            })
            .bindEvent({
                select: function(data) {
                    var index = data.ids[0];
                    data = Ox.getObject(items, 'index', index);
                    $results.replaceElement(1, Ox.LoadingScreen().start());
                    Ox.print('OLID', data.olid);
                    oml.api.getMetadata({olid: data.olid}, function(result) {
                        Ox.print('#### GOT DATA', result.data);
                        $results.replaceElement(1, oml.ui.infoView(result.data));
                        that.options('buttons')[1].options({disabled: false});
                    });
                }
            }),
            $results = Ox.SplitPanel({
                elements: [
                    {element: $list, size: 80},
                    {element: oml.ui.infoView(items[0])}
                ],
                orientation: 'vertical'
            });
        return $results;
    }

    function updateButtons() {
        var data = {}, empty, original;
        keys.forEach(function(key) {
            data[key.id] = inputValue(key.id);
        });
        empty = isEmpty(data);
        original = isOriginal(data);
        $clearButton.options({disabled: empty});
        $resetButton.options({disabled: original});
        $findButton.options({disabled: empty});
    }

    return that;

};