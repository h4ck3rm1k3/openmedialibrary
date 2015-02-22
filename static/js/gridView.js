'use strict';

oml.ui.gridView = function() {

    var ui = oml.user.ui,

        that = Ox.IconList({
            defaultRatio: oml.config.iconRatio,
            draggable: true,
            item: function(data, sort, size) {
                var color = oml.getIconInfoColor(ui.iconInfo, data).map(function(rgb) {
                        return rgb.concat(0.8);
                    }),
                    ratio = (ui.icons == 'cover' ? data.coverRatio : data.previewRatio)
                        || oml.config.iconRatio,
                    width = Math.round(ratio >= 1 ? size : size * ratio),
                    height = Math.round(ratio <= 1 ? size : size / ratio),
                    sortKey = sort[0].key,
                    info = Ox.getObjectById(oml.config.sortKeys, sortKey).format(
                        Ox.contains(['title', 'random'], sortKey)
                        ? (data.author || '') : data[sortKey]
                    );
                size = size || 128;
                return {
                    extra: ui.showIconInfo ? $('<div>')
                        .css({
                            width: width + 'px',
                            height: Math.round(size / 12.8) + 'px',
                            borderWidth: Math.round(size / 64) + 'px 0',
                            borderStyle: 'solid',
                            borderColor: 'rgba(' + color[2].join(', ') + ')',
                            margin: Math.round(size / 18) + 'px ' + Math.round(width / 2 - 14) + 'px',
                            fontSize: Math.round(size / 16) + 'px',
                            textAlign: 'center',
                            color: 'rgba(' + color[2].join(', ') + ')',
                            backgroundImage: '-webkit-linear-gradient(top, ' + color.slice(0, 2).map(function(rgba) {
                                return 'rgba(' + rgba.join(', ') + ')';
                            }).join(', ') + ')',
                            MozTransform: 'rotate(45deg)',
                            WebkitTransform: 'rotate(45deg)'
                        })
                        .html(
                            ui.iconInfo == 'extension'
                            ? data.extension.toUpperCase()
                            : Ox.formatValue(data.size, 'B')
                        ) : null,
                    height: height,
                    id: data.id,
                    info: info,
                    title: data.title,
                    url: '/' + data.id + '/' + ui.icons + '128.jpg',
                    width: width
                };
            },
            items: function(data, callback) {
                oml.api.find(Ox.extend(data, {
                    query: ui.find
                }), callback);
            },
            keys: [
                'author', 'coverRatio', 'extension', 'id', 'mediastate',
                'previewRatio', 'size', 'textsize', 'title'
            ],
            selected: ui.listSelection,
            size: 128,
            sort: Ox.clone(ui.listSort, true),
            unique: 'id'
        })
        .bindEvent({
            oml_iconinfo: function() {
                that.reloadList(true);
            },
            oml_icons: function() {
                that.reloadList(true);
            },
            oml_showiconinfo: function() {
                that.reloadList(true);
            }
        });

    return that;

};
