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
                var $content = Ox.Element(),
                    $logo = Ox.Element(),
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
                if (id == 'update') {
                    $content.html('<h1><b>' + title + '</b></h1>');
                    var $update = Ox.Element()
                        .css({
                            paddingTop: '4px',
                            paddingBottom: '16px'
                        }).appendTo($content);
                    oml.api.getVersion(function(response) {
                        if (response.data.update) {
                            if (response.data.current == 'git') {
                                $update.html('A new version of Open Media Library is available in git.<br>To update run: <code>./ctl update</code>');
                            } else {
                                $update.html('A new version of Open Media Library is available');
                                Ox.Button({
                                    id: 'update',
                                    title: Ox._('Install Now')
                                }).bindEvent({
                                    click: function() {
                                        this.options({
                                            disabled: true,
                                            title: 'Installing...'
                                        });
                                        oml.api.restart(function(response) {
                                            if (response.status.code == 200) {
                                                setTimeout(reload, 500);
                                            }
                                        });
                                    }
                                }).appendTo($content);
                            }
                        } else {
                            $update.html('No updates available')
                        }
                    });
                } else {
                    $content.html('<h1><b>' + title + '</b></h1>'
                        + '<p>The lazy brown fox jumped over the lazy black fox, but otherwise not really much happened here since you last checked.');
                }
                $('<div>')
                    .css({
                        position: 'absolute',
                        left: '16px',
                        right: '16px',
                        top: '16px',
                        overflowY: 'auto'
                    })
                    .append($content)
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
                    that.updateElement();
                }
            }
        });

    that.updateElement = function(section) {
        $panel.selectTab(section);
    };

    function reload() {
        var ws = new WebSocket('ws:' + document.location.host + '/ws');
        ws.onopen = function(event) {
            document.location.href = document.location.protocol + '//' + document.location.host;
        };
        ws.onerror = function(event) {
            ws.close();
        };
        ws.onclose = function(event) {
            console.log('waiting...');
            setTimeout(reload, 500);
        };
    }

    return that;

};
