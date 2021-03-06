#!/usr/bin/env bash
HOST="127.0.0.1:9842"
NAME="openmedialibrary"
PID="/tmp/$NAME.$USER.pid"

cd "`dirname "$0"`"
if [ -e oml ]; then
    cd ..
fi
BASE=`pwd`
SYSTEM=`uname -s`
PLATFORM=`uname -m`

if [ ! -e $PID ]; then
if [ -e "$BASE/config/tor/hostname" ]; then
    onion=$(cat "$BASE/config/tor/hostname")
    id=${onion/.onion/}
    PID="/tmp/$NAME.$USER.$id.pid"
fi
fi

if [ -e "$BASE/local_platform" ]; then
    export PLATFORM_ENV="$BASE/local_platform"
else
if [ $SYSTEM == "Linux" ]; then
    export PLATFORM_ENV="$BASE/platform/${SYSTEM}_${PLATFORM}"
else
    export PLATFORM_ENV="$BASE/platform/$SYSTEM"
fi
fi
if [ $SYSTEM == "Darwin" ]; then
    export DYLD_FALLBACK_LIBRARY_PATH="$PLATFORM_ENV/lib"
fi
PATH="$PLATFORM_ENV/bin:$PATH"

SHARED_ENV="$BASE/platform/Shared"
export SHARED_ENV

PATH="$SHARED_ENV/bin:$PATH"
export PATH

PYTHONPATH="$PLATFORM_ENV/lib/python3.4/site-packages:$SHARED_ENV/lib/python3.4/site-packages:$BASE/$NAME"
export PYTHONPATH

oxCACHE="$BASE/config/ox"
export oxCACHE

#must be called to update commands in $PATH
hash -r 2>/dev/null

# allow more open files
ulimit -S -n 2048

function remove_loginscript {
    if [ $SYSTEM == "Darwin" ]; then
        launchd_name="com.openmedialibrary.loginscript"
        launchd_plist="$HOME/Library/LaunchAgents/${launchd_name}.plist"
        if [ -e "$launchd_plist" ]; then
            launchctl stop "$launchd_name"
            launchctl unload "$launchd_plist"
            rm "$launchd_plist"
        fi
    fi
}

if [ "$1" == "start" ]; then
    remove_loginscript
    if [ $SYSTEM == "Linux" ]; then
        if [ -e "$HOME/.config/autostart/openmedialibrary.desktop" ]; then
            rm "$HOME/.config/autostart/openmedialibrary.desktop"
        fi
    fi
    cd "$BASE/$NAME"
    if [ -e $PID ]; then
        if ps -p `cat "$PID"` > /dev/null; then
            echo openmedialibrary already running
            exit 1
        fi
    fi
    if [ ! -d "$BASE/$NAME/.git" ]; then
        python3 oml install_update
        cd "$BASE/$NAME"
    fi
    exec python3 oml server $PID
fi
if [ "$1" == "debug" ]; then
    cd "$BASE/$NAME"
    if [ -e $PID ]; then
        echo openmedialibrary already running
        exit 1
    fi
    shift
    exec python3 oml server $@
fi
if [ "$1" == "stop" ]; then
    remove_loginscript
    if [ -e $PID ]; then
        _PID=`cat $PID`
        kill $_PID
        waited=0
        while ps -p $_PID > /dev/null
        do
            sleep 1
            waited=$(($waited+1))
            if [ $waited -gt 10 ]; then
                kill -9 $_PID
                sleep 1
            fi
        done
        test -e $PID && rm $PID
    fi
    exit $?
fi
if [ "$1" == "restart" ]; then
    if [ -e $PID ]; then
        "$0" stop
        "$0" start
        exit $?
    else
        "$0" start
        exit $?
    fi
fi
if [ "$1" == "open" ]; then
    if [ $SYSTEM == "Darwin" ]; then
        open "/Applications/Open Media Library.app"
    fi
    if [ $SYSTEM == "Linux" ]; then
        if [ -e $PID ]; then
            if ps -p `cat "$PID"` > /dev/null; then
                xdg-open "file://${BASE}/openmedialibrary/static/html/load.html"
            else
                exec python3 "$NAME/oml/gtkstatus.py" $@
            fi
        else
            exec python3 "$NAME/oml/gtkstatus.py" $@
        fi
    fi
    exit 0
fi
if [ "$1" == "ui" ]; then
    shift
    exec python3 "$NAME/oml/ui.py" $@
fi
if [ "$1" == "update" ]; then
    cd "$BASE/$NAME"
    if [ -d "$BASE/$NAME/.git" ]; then
        OLD=`"$0" version`
        cd "$BASE/platform"
        echo Update platform..
        git pull
        echo Update $NAME..
        cd "$BASE/$NAME"
        find . -name "*.pyc" -exec rm "{}" \;
        git pull
        "$0" update_static > /dev/null
        NEW=`"$0" version`
        "$0" postupdate -o $OLD -n $NEW
    else
        python3 oml update
    fi
    exit $?
fi
if [ "$1" == "python" ]; then
    cd "$BASE/$NAME"
    shift
    exec python3 $@
fi

cd "$BASE/$NAME"
exec python3 oml $@
