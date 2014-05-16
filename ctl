#!/usr/bin/env bash
HOST="[::1]:9842"
NAME="openmedialibrary"
PID="/tmp/$NAME.pid"

cd `dirname "$0"`
if [ -e oml ]; then
    cd ..
fi
BASE=`pwd`
SYSTEM=`uname -s`

export PLATFORM_ENV="$BASE/platform/$SYSTEM"
if [ $SYSTEM == "Darwin" ]; then
	export DYLD_FALLBACK_LIBRARY_PATH="$PLATFORM_ENV/lib"
fi
PATH="$PLATFORM_ENV/bin:$PATH"

SHARED_ENV="$BASE/platform/Shared"
export SHARED_ENV

PATH="$SHARED_ENV/bin:$PATH"
export PATH

PYTHONPATH="$PLATFORM_ENV/lib/python2.7/site-packages:$SHARED_ENV/lib/python2.7/site-packages:$BASE/$NAME"
export PYTHONPATH

oxCACHE="$BASE/config/ox"
export oxCACHE

#must be called to update commands in $PATH
hash -r 2>/dev/null

if [ "$1" == "start" ]; then
    cd $BASE/$NAME
    if [ -e $PID ]; then
        echo openmedialibrary already running
        exit 1
    fi
    python2 oml server PID &
    exit $?
fi
if [ "$1" == "debug" ]; then
    cd $BASE/$NAME
    if [ -e $PID ]; then
        echo openmedialibrary already running
        exit 1
    fi
    shift
    python2 oml server $@
    exit $?
fi
if [ "$1" == "stop" ]; then
    test -e $PID && kill `cat $PID`
    test -e $PID && rm $PID
    exit $?
fi
if [ "$1" == "restart" ]; then
    if [ -e $PID ]; then
        $0 stop
        $0 start
        exit $?
    else
        exit 1
    fi
fi
if [ "$1" == "open" ]; then
    #time to switch to python and use webbrowser.open_tab?
    if [ $SYSTEM == "Darwin" ]; then
        open http://$HOST/
    else
        xdg-open http://$HOST/
    fi
    exit 0
fi

cd $BASE/$NAME
python2 oml $@
exit $?
