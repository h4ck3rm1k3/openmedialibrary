'use strict';

oml.ui.browser = function() {

    var ui = oml.user.ui,

        that = Ox.IconList({
            centered: true,
            defaultRatio: oml.config.coverRatio,
            draggable: true,
            item: function(data, sort, size) {
                var color = oml.getFileInfoColor(ui.fileInfo, data).map(function(rgb) {
                        return rgb.concat(0.8);
                    }),
                    ratio = data.coverRatio || oml.config.coverRatio,
                    width = Math.round(ratio >= 1 ? size : size * ratio),
                    height = Math.round(ratio <= 1 ? size : size / ratio),
                    sortKey = sort[0].key,
                    info = Ox.getObjectById(oml.config.sortKeys, sortKey).format(
                        Ox.contains(['title', 'random'], sortKey)
                        ? (data.author || '') : data[sortKey]
                    );
                size = size || 64;
                return {
                    extra: ui.showFileInfo ? $('<div>')
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
                'author', 'coverRatio', 'extension', 'id',
                'mediastate', 'size', 'textsize', 'title'
            ],
            max: 1,
            min: 1,
            orientation: 'horizontal',
            // FIXME: is this correct?:
            selected: ui.item ? [ui.item]
                : ui.listSelection.length ? [ui.listSelection[0]]
                : [],
            size: 64,
            sort: ui.listSort,
            unique: 'id'
        })
        .bindEvent({
            open: function(data) {
                if (that.value(data.ids[0], 'mediastate') == 'available') {
                    oml.UI.set({itemView: 'book'});
                }
            },
            select: function(data) {
                oml.UI.set({
                    item: data.ids[0],
                    itemView: 'info',
                    listSelection: data.ids
                });
            },
            oml_find: function() {
                that.reloadList();
            },
            oml_item: function(data) {
                if (data.value && !data.previousValue) {
                    that.gainFocus();
                }
            },
            oml_listselection: function(data) {
                if (data.value.length) {
                    that.options({selected: [data.value[0]]});
                }
            },
            oml_listsort: function(data) {
                that.options({sort: data.value});
            },
            oml_sidebarsize: function(data) {
                that.size(); // FIXME: DOESN'T CENTER
            }
        });

    oml.enableDragAndDrop(that);

    return that;

};