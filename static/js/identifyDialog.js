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

        idValue, titleValue,

        $idInputs, $idButtons = {},

        $idForm = renderIdForm(data),

        $idPreview = data.mainid
            ? oml.ui.infoView(data)
            : Ox.Element(),

        $idPanel = Ox.SplitPanel({
            elements: [
                {element: Ox.Element().append($idForm), size: 96},
                {element: $idPreview}
            ],
            orientation: 'vertical'
        }),

        $titleInputs, $titleButtons = {},

        $titleForm = renderTitleForm(),

        $titlePanel = Ox.SplitPanel({
            elements: [
                {element: $titleForm, size: 96},
                {element: renderResults([])}
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
                        var edit = Ox.extend(
                            {id: data.id},
                            $innerPanel.options('selected') == 'id'
                                ? idValue
                                : titleValue
                        );
                        that.options({content: Ox.LoadingScreen().start()});
                        that.disableButtons();
                        oml.api.edit(edit, function(result) {
                            Ox.print('EDITED', result.data);
                            that.close();
                            Ox.Request.clearCache('find');
                            oml.$ui.browser.reloadList(true);
                            Ox.Request.clearCache(data.id);
                            oml.$ui.infoView.updateElement(result.data);
                        });
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
            // FIXME: CONCAT HERE
            var items = result.data.items.map(function(item, index) {
                    return Ox.extend({index: (index + 1).toString()}, item);
                });
            $titlePanel.replaceElement(1, renderResults(items));
        });
    }

    function getMetadata(key, value) {
        $idPanel.replaceElement(1, Ox.LoadingScreen().start());
        oml.api.getMetadata(Ox.extend({}, key, value), function(result) {
            Ox.print('GOT RESULT', result.data);
            $idForm = renderIdForm(result.data);
            $idPreview = oml.ui.infoView(result.data);
            $idPanel
                .replaceElement(0, $idForm)
                .replaceElement(1, $idPreview);
        });
    }

    function idInputValues(key, values) {
        Ox.print('WTF,', $idInputs);
        var $input = $idInputs[ids.map(function(id) {
                return id.id;
            }).indexOf(key)];
        if (Ox.isUndefined(values)) {
            values = $input.options('elements').map(function($element) {
                return $element.value();
            });
        } else {
            $input.options('elements').forEach(function($element, index) {
                $element.value(values[index]);
            });
        }
        return values;    
    }

    function titleInputValue(key, value) {
        var $input =  $titleInputs[keys.map(function(key) {
                return key.id;
            }).indexOf(key)];
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
        var $element = Ox.Element();
        $idInputs = ids.map(function(id, index) {
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
                            var value = $idInputs[index].options('elements')[1].value();
                            if (data.value) {
                                if (value) {
                                    idValue = Ox.extend({}, id.id, value);
                                    $idInputs.forEach(function($input, i) {
                                        if (i != index) {
                                            $input.options('elements')[0].value(false);
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
                                idValue = Ox.extend({}, id.id, data.value);
                                $idInputs.forEach(function($input, i) {
                                    $input.options('elements')[0].options({
                                        disabled: true,
                                        value: i == index
                                    });
                                    $input.options('elements')[1].options({
                                        disabled: true
                                    });
                                });
                                getMetadata(id.id, data.value, function() {
                                    // ...
                                    updateIdButtons();
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
        });
        $idButtons.clear = Ox.Button({
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
                    ids.forEach(function(id) {
                        idInputValues(id.id, [false, '']);
                    });
                    updateIdButtons();
                }
            })
            .appendTo($element);
        $idButtons.reset = Ox.Button({
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
                    ids.forEach(function(id) {
                        idInputValues(id.id, [
                            id.id == originalData.mainid,
                            originalData[id.id]
                        ]);
                    });
                    updateIdButtons();
                }
            })
            .appendTo($element);
        $idButtons.find = Ox.Button({
                title: Ox._('Look Up'),
                width: 64
            })
            .css({
                position: 'absolute',
                right: '16px',
                top: '64px'
            })
            .bindEvent({
                click: function() {
                    Ox.print('NOT IMPLEMENTED')
                }
            })
            .appendTo($element);
        return $element;
    }

    function renderResults(items) {
        Ox.print('LIST ITEMS::::', items);
        var $list = Ox.TableList({
                columns: [
                    {
                        format: function(value) {
                            return Ox.getObjectById(ids, value).title;
                        },
                        id: 'mainid',
                        visible: true,
                        width: 64
                    },
                    {
                        format: function(value, data) {
                            return data[data.mainid]; 
                        },
                        id: 'index',
                        visible: true,
                        width: 128 - Ox.UI.SCROLLBAR_SIZE
                    }
                ],
                items: items,
                keys: ['mainid', 'isbn10', 'isbn13'],
                min: 1,
                max: 1,
                scrollbarVisible: true,
                sort: [{key: 'mainid', operator: '+'}],
                unique: 'index'
            })
            .bindEvent({
                select: function(data) {
                    var index = data.ids[0], mainid;
                    mainid = $list.value(index, 'mainid');
                    Ox.print('MAINID', mainid)
                    titleValue = Ox.extend({}, mainid, $list.value(index, mainid));
                    $results.replaceElement(1, Ox.LoadingScreen().start());
                    oml.api.getMetadata(titleValue, function(result) {
                        if (index == $list.options('selected')[0]) {
                            $results.replaceElement(1, oml.ui.infoView(result.data));
                            that.options('buttons')[1].options({disabled: false});
                        }
                    });
                }
            }),
            $results = Ox.SplitPanel({
                elements: [
                    {element: $list, size: 192},
                    {element: Ox.Element()}
                ],
                orientation: 'horizontal'
            });
        return $results;
    }

    function renderTitleForm() {
        var $element = Ox.Element();
        $titleInputs = keys.map(function(key, index) {
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
                        $titleButtons.find.triggerEvent('click');
                    }
                })
                .appendTo($element);
        });
        $titleButtons.clear = Ox.Button({
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
                        titleInputValue(key.id, '');
                    });
                    updateTitleButtons();
                }
            })
            .appendTo($element);
        $titleButtons.reset = Ox.Button({
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
                        titleInputValue(key.id, originalData[key.id]);
                    });
                    updateTitleButtons();
                }
            })
            .appendTo($element);
        $titleButtons.find = Ox.Button({
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
                        data[key.id] = titleInputValue(key.id);
                    });
                    findMetadata(data);
                }
            })
            .appendTo($element);
        return $element;
    }

    function updateIdButtons() {
        var data = {}, empty, original;
        ids.forEach(function(id) {
            data[id.id] = idInputValues(id.id)[1];
        });
        empty = isEmpty(data);
        original = isOriginal(data);
        $idButtons.clear.options({disabled: empty});
        $idButtons.reset.options({disabled: original});
        $idButtons.find.options({disabled: empty});
        that[original ? 'disableButton' : 'enableButton']('update');
    }

    function updateTitleButtons() {
        var data = {}, empty, original;
        keys.forEach(function(key) {
            data[key.id] = titleInputValue(key.id);
        });
        empty = isEmpty(data);
        original = isOriginal(data);
        $titleButtons.clear.options({disabled: empty});
        $titleButtons.reset.options({disabled: original});
        $titleButtons.find.options({disabled: empty});
        that[original ? 'disableButton' : 'enableButton']('update');
    }

    return that;

};
