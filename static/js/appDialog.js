'use strict';

oml.ui.appDialog = function() {

    var ui = oml.user.ui,

        tabs = Ox.getObjectById(oml.config.pages, 'app').parts.map(function(tab) {
            return {
                id: tab.id,
                title: tab.title.replace(/ Open Media Library$/, ''),
                selected: tab.id == ui.part.app
            };
        }),

        $panel = Ox.TabPanel({
            content: function(id) {
                var $logo = Ox.Element(),
                    $text = Ox.Element()
                        .addClass('OxTextPage'),
                    title = Ox.getObjectById(
                        Ox.getObjectById(oml.config.pages, 'app').parts,
                        id
                    ).title;
                $('<img>')
                    .attr({
                        src: '/static/png/oml.png'
                    })
                    .css({
                        position: 'absolute',
                        left: '16px',
                        top: '16px',
                        width: '192px',
                        height: '192px'
                    })
                    .appendTo($logo);
                $('<div>')
                    .css({
                        position: 'absolute',
                        left: '16px',
                        right: '16px',
                        top: '16px',
                        overflowY: 'auto'
                    })
                    .html(
                        '<h1><b>' + title + '</b></h1>'
                        + '<p>The lazy brown fox jumped over the lazy black fox, but otherwise not really much happened here since you last checked.'
                    )
                    .appendTo($text);
                return Ox.SplitPanel({
                    elements: [
                        {
                            element: $logo,
                            size: 208
                        },
                        {
                            element: $text
                        }
                    ],
                    orientation: 'horizontal'
                });
            },
            tabs: tabs
        })
        .bindEvent({
            change: function(data) {
                oml.UI.set({'part.app': data.selected});
            }
        }),

        that = Ox.Dialog({
            buttons: [
                Ox.Button({
                    id: 'close',
                    title: Ox._('Close')
                }).bindEvent({
                    click: function() {
                        that.close();
                    }
                })
            ],
            closeButton: true,
            content: $panel,
            fixedSize: true,
            height: 384,
            removeOnClose: true,
            title: 'Open Media Library',
            width: 768
        })
        .bindEvent({
            close: function() {
                if (ui.page == 'app') {
                    oml.UI.set({page: ''});
                }
            },
            'oml_part.app': function() {
                if (ui.page == 'app') {
                    that.update();
                }
            }
        });

    that.update = function(section) {
        $panel.selectTab(section);
    };

    return that;

};