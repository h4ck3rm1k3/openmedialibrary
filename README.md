Open Media Library
==================

Install
-------

 To install the latest release on Linux run:

 curl https://git.0x2620.org/openmedialibrary.git/HEAD:/install | python2

 on Mac OS X download this:

 http://downloads.openmedialibrary.com/Open%20Media%20Library.dmg

Networking
----------

At this time you need a working IPv6 connection to use Open Media Libary.
If you dont have native IPv6 you can use Teredo/Miredo (`apt-get install miredo`)
or get a tunnel Hurricane Electric (https://tunnelbroker.net/)
or SixSS (https://sixxs.net).

Development
-----------

Now checkout the source and prepare for use:

    mkdir openmedialibrary
    cd openmedialibrary
    git clone https://git.0x2620.org/openmedialibrary.git
    git clone https://git.0x2620.org/openmedialibrary_platform.git platform
    ln -s openmedialibrary/ctl ctl
    ./ctl update_static

    # and start it
    ./ctl debug

To update to latest version:

    ./ctl update

On Linux you need a working python2 installation with pillow, pyhon-lxml and poppler-utils:

    apt-get install python3.4 python3-pil python3-lxml poppler-utils


Platform
----------

If you install Open Media Library on a architecture/os that is currently
not upported, you need a working python 2.7 installation and the dependencies
listed in requirements.txt and requirements-shared.txt:

    pip install -r requirements.txt
    pip install -r requirements-shared.txt

