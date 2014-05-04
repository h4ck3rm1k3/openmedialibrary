'use strict';

oml.ui.gridView = function() {

    var ui = oml.user.ui,

        that = Ox.IconList({
            defaultRatio: oml.config.coverRatio,
            draggable: true,
            item: function(data, sort, size) {
                var color = oml.getFileTypeColor(data).map(function(rgb) {
                        return rgb.concat(0.8)
                    }),
                    ratio = data.coverRatio || oml.config.coverRatio,
                    width = Math.round(ratio >= 1 ? size : size * ratio),
                    height = Math.round(ratio <= 1 ? size : size / ratio),
                    sortKey = sort[0].key,
                    info = Ox.getObjectById(oml.config.sortKeys, sortKey).format(
                        Ox.contains(['title', 'random'], sortKey)
                        ? (data.author || '') : data[sortKey]
                    );
                size = size || 128;
                return {
                    extra: ui.showFileInfo ? $('<div>')
                        .css({
                            width: width + 'px',
                            height: Math.round(size / 12.8) + 'px',
                            borderWidth: Math.round(size / 64) + 'px 0',
                            borderStyle: 'solid',
                            borderColor: 'rgba(' + color[1].join(', ') + ')',
                            margin: Math.round(size / 18) + 'px ' + Math.round(width / 3) + 'px',
                            fontSize: Math.round(size / 16) + 'px',
                            textAlign: 'center',
                            color: 'rgba(' + color[1].join(', ') + ')',
                            backgroundColor: 'rgba(' + color[0].join(', ') + ')',
                            WebkitTransform: 'rotate(45deg)'
                        })
                        .html(
                            ui.fileInfo == 'extension'
                            ? data.extension.toUpperCase()
                            : Ox.formatValue(data.size, 'B')
                        ) : null,
                    height: height,
                    id: data.id,
                    info: info,
                    title: data.title,
                    url: '/' + data.id + '/cover128.jpg',
                    width: width
                };
            },
            items: function(data, callback) {
                oml.api.find(Ox.extend(data, {
                    query: ui.find
                }), callback);
            },
            keys: [
                'author', 'coverRatio', 'extension',
                'id', 'size', 'textsize', 'title'
            ],
            selected: ui.listSelection,
            size: 128,
            sort: ui.listSort,
            unique: 'id'
        });

    return that;

};