'use strict';

oml.ui.identifyDialog = function(data) {

    var ui = oml.user.ui,

        lookupItems = [
            'isbn', 'asin', 'lccn', 'oclc', 'olid'
        ].map(function(id) {
            return {
                id: id,
                title: Ox.getObjectById(oml.config.itemKeys, id).title
            };
        }),

        selected = data.primaryid ? 'lookup' : 'find',

        $lookupForm = Ox.Element(),

        $lookupSelect = Ox.Select({
                items: lookupItems,
                overlap: 'right',
                max: 1,
                min: 1,
                value: data.primaryid ? data.primaryid[0] : 'isbn',
                width: 128
            })
            .bindEvent({
                change: function(data) {
                    $lookupInput.focusInput(true);
                }
            }),

        $lookupInput = Ox.Input({
                value: data.primaryid ? data.primaryid[1] : '',
                width: 480
            })
            .bindEvent({
                change: function(data) {
                    // ...
                },
                submit: lookupMetadata
            }),

        $lookupButton = Ox.Button({
                overlap: 'left',
                title: Ox._('Look Up'),
                width: 128
            })
            .bindEvent({
                click: lookupMetadata
            }),

        $lookupElement = Ox.FormElementGroup({
                elements: [
                    Ox.FormElementGroup({
                        elements: [
                            $lookupSelect,
                            $lookupInput
                        ],
                        float: 'left'
                    }),
                    $lookupButton
                ],
                float: 'right'
            })
            .css({
                margin: '16px'
            })
            .appendTo($lookupForm),

        $lookupPreview = data.primaryid
            ? oml.ui.infoView(data)
            : Ox.Element(),

        $lookupPanel = Ox.SplitPanel({
            elements: [
                {element: $lookupForm, size: 48},
                {element: $lookupPreview}
            ],
            orientation: 'vertical'
        }),

        $findForm = Ox.Element(),

        $findInput = Ox.Input({
                label: Ox._('Title, Author etc.'),
                labelWidth: 128,
                width: 608,
                value: [data.title].concat(data.author || []).join(' ')
            })
            .bindEvent({
                submit: findMetadata
            }),

        $findButton = Ox.Button({
                overlap: 'left',
                title: Ox._('Find'),
                width: 128
            })
            .bindEvent({
                click: findMetadata
            }),

        $findElement = Ox.FormElementGroup({
                elements: [
                    $findInput,
                    $findButton
                ],
                float: 'right'
            })
            .css({
                margin: '16px'
            })
            .appendTo($findForm),

        $findList,

        $findPanel = Ox.SplitPanel({
            elements: [
                {element: $findForm, size: 48},
                {element: renderResults([])}
            ],
            orientation: 'vertical'
        }),

        $bar = Ox.Bar({size: 24}),

        $buttons = Ox.ButtonGroup({
                buttons: [
                    {id: 'lookup', title: Ox._('Look Up by ID')},
                    {id: 'find', title: Ox._('Find by Title')}
                ],
                selectable: true,
                value: selected
            })
            .css({
                width: '768px',
                padding: '4px 0',
                textAlign: 'center'
            })
            .bindEvent({
                change: function(data) {
                    selected = data.value;
                    $innerPanel.options({selected: selected});
                    $updateButton.options({
                        disabled: selected == 'find' && !$findList
                    });
                }
            })
            .appendTo($bar),

        $innerPanel = Ox.SlidePanel({
            elements: [
                {id: 'lookup', element: $lookupPanel},
                {id: 'find', element: $findPanel}
            ],
            orientation: 'horizontal',
            selected: selected,
            size: 768
        }),

        $outerPanel = Ox.SplitPanel({
            elements: [
                {element: $bar, size: 24},
                {element: $innerPanel}
            ],
            orientation: 'vertical'
        }),

        $metadataSelect = Ox.Select({
                items: [
                    {id: 'original', title: Ox._('Show Original Metadata')},
                    {id: 'edited', title: Ox._('Show Edited Metadata')}
                ],
                max: 1,
                min: 1,
                value: 'edited',
                width: 192
            })
            .css({
                margin: '4px'
            })
            .bindEvent({
                change: function(data) {
                    if (selected == 'lookup') {
                        if (!$lookupButton.options('disabled')) {
                            $lookupButton.triggerEvent('click');
                        }
                    } else {
                        if ($findList) {
                            $findList.triggerEvent('select', {
                                ids: $findList.options('selected')
                            });
                        }
                    }
                }
            }),

        $dontUpdateButton = Ox.Button({
                id: 'dontupdate',
                title: Ox._('No, Don\'t Update')
            })
            .bindEvent({
                click: function() {
                    that.close();
                }
            }),

        $updateButton = Ox.Button({
                disabled: true,
                id: 'update',
                title: Ox._('Yes, Update')
            })
            .bindEvent({
                click: function() {
                    // FIXME: Wrong if user messes with lookup elements before clicking update button
                    var primaryId;
                    if (selected == 'lookup') {
                        primaryId = [
                            $lookupSelect.value(),
                            $lookupInput.value()
                        ];
                    } else {
                        primaryId = $findList.value(
                            $findList.options('selected')[0],
                            'primaryid'
                        );
                    }
                    that.options({content: Ox.LoadingScreen().start()});
                    that.disableButtons();
                    oml.api.edit({
                        id: data.id,
                        primaryid: primaryId
                    }, function(result) {
                        (
                            $metadataSelect.value() == 'original'
                            ? oml.api.resetMetadata : Ox.noop
                        )({id: ui.item}, function(result) {
                            that.close();
                            Ox.Request.clearCache('find');
                            oml.$ui.browser.reloadList(true);
                            Ox.Request.clearCache(data.id);
                            oml.$ui.infoView.updateElement(data.id);
                        });
                    });
                }
            }),

        that = Ox.Dialog({
            buttons: [
                $dontUpdateButton,
                $updateButton
            ],
            closeButton: true,
            content: $outerPanel,
            fixedSize: true,
            height: 384,
            removeOnClose: true,
            title: Ox._('Identify Book'),
            width: 768
        });

    $($metadataSelect.find('.OxButton')[0]).css({margin: 0});
    $metadataSelect.appendTo($(that.find('.OxBar')[2]));

    function disableButtons() {
        $lookupSelect.options('items').forEach(function(item) {
            $lookupSelect.disableItem(item.id);
        });
        $lookupInput.options({disabled: true});
        $lookupButton.options({disabled: true});
        $findInput.options({disabled: true});
        $findButton.options({disabled: true});
        $metadataSelect.options('items').forEach(function(item) {
            $metadataSelect.disableItem(item.id);
        });
        $updateButton.options({disabled: true});
    }

    function enableButtons() {
        $lookupSelect.options('items').forEach(function(item) {
            $lookupSelect.enableItem(item.id);
        });
        $lookupInput.options({disabled: false});
        $lookupButton.options({disabled: false});
        $findInput.options({disabled: false});
        $findButton.options({disabled: false});
        $metadataSelect.options('items').forEach(function(item) {
            $metadataSelect.enableItem(item.id);
        });
        $updateButton.options({disabled: false});
    }

    function findMetadata() {
        disableButtons();
        $findPanel.replaceElement(1, Ox.LoadingScreen().start());
        oml.api.findMetadata({
            query: $findInput.value()
        }, function(result) {
            var items = result.data.items.map(function(item, index) {
                return Ox.extend({index: index.toString()}, item);
            });
            enableButtons();
            $updateButton.options({disabled: !items.length});
            $findPanel.replaceElement(1, renderResults(items));
        });
    }

    function lookupMetadata() {
        disableButtons();
        $lookupPanel.replaceElement(1, Ox.LoadingScreen().start());
        oml.api.getMetadata(Ox.extend(
            {includeEdits: $metadataSelect.value() == 'edited'},
            $lookupSelect.value(),
            $lookupInput.value()
        ), function(result) {
            enableButtons();
            $updateButton.options({disabled: Ox.isEmpty(data)});
            $lookupPreview = Ox.isEmpty(data)
                ? Ox.Element()
                : oml.ui.infoView(result.data);
            $lookupPanel.replaceElement(1, $lookupPreview);
        });
    }

    function renderResults(items) {
        var $resultsPanel;
        if (items.length) {
            $findList = Ox.TableList({
                    columns: [{
                        format: function(value, data) {
                            return '<b>' + Ox.getObjectById(
                                lookupItems, data.primaryid[0]
                            ).title + ':</b> ' + data.primaryid[1]
                        },
                        id: 'index',
                        visible: true,
                        width: 192 - Ox.UI.SCROLLBAR_SIZE
                    }],
                    items: items,
                    keys: ['primaryid'].concat(lookupItems.map(function(item) {
                        return item.id;
                    })),
                    min: 1,
                    max: 1,
                    scrollbarVisible: true,
                    selected: ['0'],
                    sort: [{key: 'index', operator: '+'}],
                    unique: 'index'
                })
                .bindEvent({
                    select: function(data) {
                        var index = data.ids[0],
                            primaryId = $findList.value(index, 'primaryid');
                        disableButtons();
                        $resultsPanel.replaceElement(1, Ox.LoadingScreen().start());
                        oml.api.getMetadata(Ox.extend(
                            {includeEdits: $metadataSelect.value() == 'edited'},
                            primaryId[0],
                            primaryId[1]
                        ), function(result) {
                            enableButtons();
                            $resultsPanel.replaceElement(1, oml.ui.infoView(result.data));
                        });
                    }
                }),
            $resultsPanel = Ox.SplitPanel({
                elements: [
                    {element: $findList || Ox.Element(), size: 192},
                    {element: Ox.Element()}
                ],
                orientation: 'horizontal'
            });
            setTimeout(function() {
                $findList.triggerEvent('select', {ids: ['0']});
            });
        } else {
            $findList = void 0;
            $resultsPanel = Ox.Element();
        }
        return $resultsPanel;
    }

    return that;

};
