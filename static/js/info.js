'use strict';

oml.ui.info = function() {

    var ui = oml.user.ui,

        that = Ox.Element()
            .addClass('OxTextPage')
            .css({
                padding: '0 16px',
                textAlign: 'center',
                overflowY: 'auto'
            })
            .bindEvent({
                toggle: function(data) {
                    oml.UI.set({showInfo: !data.collapsed});
                },
                oml_item: function() {
                    that.updateElement();
                },
                oml_listselection: function() {
                    that.updateElement();
                }
            });

    that.updateElement = function() {
        var id = ui.item || ui.listSelection[0];
        if (id) {
            oml.api.get({
                id: id,
                keys: [
                    'author', 'coverRatio',
                    'description', 'modified', 'title'
                ]
            }, function(result) {
                var data = result.data;
                that.empty();
                $('<img>')
                    .attr({src: '/' + id + '/cover128.jpg?' + data.modified})
                    .css({margin: '16px 0 8px 0'})
                    .appendTo(that);
                $('<div>')
                    .css({
                        fontWeight: 'bold'
                    })
                    .html(data.title || '')
                    .appendTo(that);
                $('<div>')
                    .css({
                        fontWeight: 'bold'
                    })
                    .html((data.author || []).join(', '))
                    .appendTo(that);
                $('<div>')
                    .css({marginTop: '8px'})
                    .html(
                        Ox.encodeHTMLEntities(result.data.description || '')
                    )
                    .appendTo(that);
                $('<div>')
                    .css({height: '16px'})
                    .appendTo(that);
            });
        } else {
            that.empty();
        }
        return that;
    };

    return that.updateElement();

};
