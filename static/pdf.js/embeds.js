Ox.load({
    UI: {
        loadCSS: false
    }
}, function() {
    var currentPage = PDFView.page;
    window.addEventListener('pagechange', function (evt) {
        var page = evt.pageNumber;
        if (page && page != currentPage) {
            currentPage = page;
            Ox.$parent.postMessage('page', {
                page: Math.round(page)
            });
        }
    });
    Ox.$parent.bindMessage({
        page: function(data) {
            if (data.page != PDFView.page) {
                PDFView.page = data.page;
            }
        },
        pdf: function(data) {
            if (PDFView.url != data.pdf) {
                PDFView.open(data.pdf);
            }
        }
    });
});

function getVideoOverlay(page) {
    var links = (window.embeds || []).filter(function(embed) {
        return embed.page == page && embed.type =='inline';
    });
    return (window.editable || links.length) ? {
        beginLayout: function() {
            this.counter = 0;
        },
        endLayout: function() {
        },
        appendImage: function(image) {
            var id = ++this.counter,
                video = links.filter(function(embed) {
                    return embed.id == id;
                })[0],
                $interface, $playButton, $editButton;
            if (editable || video) {
                $interface = Ox.$('<div>')
                    .addClass('interface')
                    .css({
                        left: image.left + 'px',
                        top: image.top + 'px',
                        width: image.width + 'px',
                        height: image.height + 'px'
                    });
                $playButton = Ox.$('<img>')
                    .addClass('button playButton')
                    .attr({
                        src: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNTYiIGhlaWdodD0iMjU2Ij48cG9seWdvbiBwb2ludHM9IjU2LDMyIDI0OCwxMjggNTYsMjI0IiBmaWxsPSIjRkZGRkZGIi8+PC9zdmc+PCEtLXsiY29sb3IiOiJ2aWRlbyIsIm5hbWUiOiJzeW1ib2xQbGF5IiwidGhlbWUiOiJveGRhcmsifS0tPg=='
                    })
                    .hide()
                    .appendTo($interface);
                $editButton = Ox.$('<img>')
                    .addClass('button editButton')
                    .attr({
                        src: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNTYiIGhlaWdodD0iMjU2Ij48cG9seWdvbiBwb2ludHM9IjMyLDIyNCA2NCwxNjAgOTYsMTkyIiBmaWxsPSIjRkZGRkZGIi8+PGxpbmUgeDE9Ijg4IiB5MT0iMTY4IiB4Mj0iMTg0IiB5Mj0iNzIiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSI0OCIvPjxsaW5lIHgxPSIxOTIiIHkxPSI2NCIgeDI9IjIwOCIgeTI9IjQ4IiBzdHJva2U9IiNGRkZGRkYiIHN0cm9rZS13aWR0aD0iNDgiLz48bGluZSB4MT0iMTEyIiB5MT0iMjIwIiB4Mj0iMjI0IiB5Mj0iMjIwIiBzdHJva2U9IiNGRkZGRkYiIHN0cm9rZS13aWR0aD0iOCIvPjxsaW5lIHgxPSIxMjgiIHkxPSIyMDQiIHgyPSIyMjQiIHkyPSIyMDQiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSI4Ii8+PGxpbmUgeDE9IjE0NCIgeTE9IjE4OCIgeDI9IjIyNCIgeTI9IjE4OCIgc3Ryb2tlPSIjRkZGRkZGIiBzdHJva2Utd2lkdGg9IjgiLz48L3N2Zz4=',
                        title: 'Click to add video'
                    })
                    .on({click: edit})
                    .hide()
                    .appendTo($interface);
                if (editable) {
                    $editButton.show();
                }
                if (video) {
                    enableVideoUI();
                }
                this.div.appendChild($interface[0]);
                Ox.$parent.bindMessage('update', function(data) {
                    if (video && data.id == video.id && data.page == video.page) {
                        video.src = data.src;
                        video.src !== '' ? enableVideoUI() : disableVideoUI();
                    }
                });
            }
            function play(e) {
                e.preventDefault();
                e.stopPropagation();
                var videoId = 'video' + page + id + Ox.uid(),
                    $iframe = Ox.Element('<iframe>')
                        .attr({
                            id: videoId,
                            src: video.src
                                + (video.src.indexOf('?') == -1 ? '?' : '&')
                                + '&showCloseButton=true&fullscreen=false&paused=false',
                            width: '100%',
                            height: '100%',
                            frameborder: 0
                        })
                        .bindMessage({
                            close: function(data) {
                                if(!closed) {
                                    closed = true;
                                    $iframe.remove();
                                    delete $iframe;
                                    $playButton.show();
                                    $editButton.show();
                                }
                            }
                        })
                        .appendTo($interface),
                    closed = false;
                $playButton.hide();
                $editButton.hide();
                return false;
            }
            function edit(e) {
                var url;
                e.preventDefault();
                e.stopPropagation();
                video = video || {
                    id: id,
                    page: page,
                    src: '',
                    type: 'inline'
                };
                Ox.$parent.postMessage('edit', video);
                return false;
            }
            function enableVideoUI() {
                $interface
                    .addClass('video')
                    .attr({title: 'Click to play video'})
                    .on({click: play});
                $playButton.show();
                $editButton.attr({title: 'Click to edit or remove video'});
            }
            function disableVideoUI() {
                $interface
                    .removeClass('video')
                    .attr({title: ''})
                    .off({click: play});
                $playButton.hide();
                $editButton.attr({title: 'Click to add video'});
            }
        }
    } : null;
}
