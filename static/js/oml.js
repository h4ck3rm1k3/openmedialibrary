'use strict';

(function() {

    var animationInterval,
        enableDebugMode = getLocalStorage('oml.enableDebugMode'),
        omlVersion = getOMLVersion(),
        oxjsPath = '/static/oxjs/' + (enableDebugMode ? 'dev' : 'build'),
        terminal,
        theme = getLocalStorage('Ox.theme')
            && JSON.parse(localStorage['Ox.theme'])
            || 'oxlight';

    loadImages(function(images) {
        loadScreen(images);
        loadOxJS(loadOML);
    });

    function getLocalStorage(key) {
        try {
            return localStorage[key];
        } catch(e) {}
    }

    function getOMLVersion() {
        var i, path, scripts = document.getElementsByTagName('script');
        for (i = 0; i < scripts.length; i++) {
            if(/oml.js/.test(scripts[i].src)) {
                return scripts[i].src.replace(/.*\?/, '');
            }
        }
    }

    function initOML(data) {
        Ox.extend(oml, {
            $ui: {},
            config: data.config,
            user: data.user
        });
        // make sure all valid ui settings are present
        oml.user.ui = Ox.extend(
            Ox.clone(data.config.user.ui, true),
            oml.user.ui
        );
        // make sure no invalid ui settings are present
        Object.keys(oml.user.ui).forEach(function(key) {
            if (Ox.isUndefined(oml.config.user.ui[key])) {
                delete oml.user.ui[key];
            }
        });
        // TODO: make sure listView, listSort and itemView are valid
        Ox.extend(oml.config, {
            filters: oml.config.itemKeys.filter(function(key) {
                return key.filter;
            }).map(function(key) {
                return {
                    id: key.id,
                    title: key.title,
                    type: Ox.isArray(key.type) ? key.type[0] : key.type
                };
            }),
            findKeys: oml.config.itemKeys.filter(function(key) {
                return key.find;
            }),
            sortKeys: oml.config.itemKeys.filter(function(key) {
                return key.sort && key.columnWidth;
            }).map(function(key) {
                return Ox.extend({
                    operator: oml.getSortOperator(key.id)
                }, key, {
                    format: function(value) {
                        return key.format
                            ? Ox['format' + Ox.toTitleCase(key.format.type)].apply(
                                this, [value].concat(key.format.args || [])
                            )
                            : Ox.isArray(key.type) ? (value || []).join(', ')
                            : (value || '');
                    }
                });
            })
        });
        oml.config.listSettings = {};
        Ox.forEach(oml.config.user.ui, function(value, key) {
            if (/^list[A-Z]/.test(key)) {
                oml.config.listSettings[key] = key[4].toLowerCase() + key.slice(5);
            }
        });
        oml.URL.init().parse(function() {
            oml.clipboard = Ox.Clipboard();
            oml.history = Ox.History();
            oml.$ui.appPanel = oml.ui.appPanel().appendTo(Ox.$body);
            oml.$ui.loadingIcon.update(Ox.Request.requests());
            Ox.Request.bindEvent({
                error: function(data) {
                    oml.$ui.errorDialog = oml.ui.errorDialog().update(data).open();
                },
                request: function(data) {
                    oml.$ui.loadingIcon.update(data.requests);
                }
            });
             if (oml.user.preferences.extensions) {
                try {
                    eval(oml.user.preferences.extensions)
                } catch(e) {}
            }
            removeScreen();
        });
    }

    function loadImages(callback) {
        var images = {};
        images.logo = document.createElement('img');
        images.logo.onload = function() {
            images.logo.style.position = 'absolute';
            images.logo.style.left = 0;
            images.logo.style.top = 0;
            images.logo.style.right = 0;
            images.logo.style.bottom = '96px';
            images.logo.style.width = '256px';
            images.logo.style.height = '256px';
            images.logo.style.margin = 'auto';
            images.logo.style.MozUserSelect = 'none';
            images.logo.style.MSUserSelect = 'none';
            images.logo.style.OUserSelect = 'none';
            images.logo.style.WebkitUserSelect = 'none';
            images.loadingIcon = document.createElement('img');
            images.loadingIcon.setAttribute('id', 'loadingIcon');
            images.loadingIcon.style.position = 'absolute';
            images.loadingIcon.style.left = 0;
            images.loadingIcon.style.top = '256px'
            images.loadingIcon.style.right = 0;
            images.loadingIcon.style.bottom = 0;
            images.loadingIcon.style.width = '32px';
            images.loadingIcon.style.height = '32px';
            images.loadingIcon.style.margin = 'auto';
            images.loadingIcon.style.MozUserSelect = 'none';
            images.loadingIcon.style.MSUserSelect = 'none';
            images.loadingIcon.style.OUserSelect = 'none';
            images.loadingIcon.style.WebkitUserSelect = 'none';
            images.loadingIcon.src = oxjsPath
                + '/Ox.UI/themes/' + theme + '/svg/symbolLoading.svg';
            callback(images);
        };
        images.logo.src = '/static/png/oml.png';
    }

    function loadOML(browserSupported) {
        window.oml = Ox.App({
            name: 'oml',
            socket: 'ws://' + document.location.host + '/ws',
            url: '/api/'
        }).bindEvent({
            load: function(data) {
                data.browserSupported = browserSupported;
                oml.ui = {};
                loadOMLFiles(function() {
                    initOML(data);
                });
            }
        });
    }

    function loadOMLFiles(callback) {
        var path = '/static/';
        if (enableDebugMode) {
            Ox.getJSON(path + 'json/js.json?' + Ox.random(1000000), function(files) {
                Ox.getFile(files.map(function(file) {
                    return path + 'js/' + file + '?' + omlVersion;
                }), callback);
            });
        } else {
            Ox.getScript(path + 'js/oml.min.js?' + omlVersion, callback);
        }
    }

    function loadOxJS(callback) {
        var head = document.head
                || document.getElementsByTagName('head')[0]
                || document.documentElement, 
            script = document.createElement('script');
        script.onload = function() {
            Ox.load({UI: {theme: theme}}, callback);
        };
        script.src = oxjsPath + '/Ox.js?' + omlVersion;
        script.type = 'text/javascript';
        head.appendChild(script);
    }

    function loadScreen(images) {
        var loadingScreen = document.createElement('div');
        loadingScreen.setAttribute('id', 'loadingScreen');
        loadingScreen.className = 'OxScreen';
        loadingScreen.style.position = 'absolute';
        loadingScreen.style.width = '100%';
        loadingScreen.style.height = '100%';
        loadingScreen.style.backgroundColor = theme == 'oxlight' ? 'rgb(224, 224, 224)'
            : theme == 'oxmedium' ? 'rgb(144, 144, 144)' : 'rgb(32, 32, 32)';
        loadingScreen.style.zIndex = '1002';
        loadingScreen.appendChild(images.logo);
        loadingScreen.appendChild(images.loadingIcon);
        // FF3.6 document.body can be undefined here
        window.onload = function() {
            document.body.style.margin = 0;
            document.body.appendChild(loadingScreen);
            startAnimation();
        };
        // IE8 does not call onload if already loaded before set
        document.body && window.onload();
    }

    function loadTerminal() {
        terminal = document.createElement('div');
        terminal.style.display = 'none';
        terminal.style.position = 'absolute';
        terminal.style.width = '100%';
        terminal.style.height = '100%';
        terminal.style.zIndex = '1003';
    }

    function log(message) {
        var line = document.createElement('div');
        line.innerHTML = message;
        terminal.appendChild(line);
    }

    function removeScreen() {
        var $loadingScreen = $('#loadingScreen');
        $loadingScreen.animate({
            opacity: 0
        }, 1000, function() {
            $loadingScreen.remove();
        });
    }

    function startAnimation() {
        var css, deg = 0, loadingIcon = document.getElementById('loadingIcon'),
            previousTime = +new Date();
        animationInterval = setInterval(function() {
            var currentTime = +new Date(),
                delta = (currentTime - previousTime) / 1000;
            previousTime = currentTime;
            deg = Math.round((deg + delta * 360) % 360 / 30) * 30;
            css = 'rotate(' + deg + 'deg)';
            loadingIcon.style.MozTransform = css;
            loadingIcon.style.MSTransform = css;
            loadingIcon.style.OTransform = css;
            loadingIcon.style.WebkitTransform = css;
            loadingIcon.style.transform = css;
        }, 83);
    }

    function stopAnimation() {
        clearInterval(animationInterval);
    }

}());
