Open Media Library
==================

Install
-------

 soon

Networking
----------

At this time you need a working IPv6 connection to use Open Media Libary.
If you dont have native IPv6 you can use Teredo/Miredo (apt-get install miredo)
or get a tunnel Hurricane Electric (https://tunnelbroker.net/)
or SixSS (https://sixxs.net).

Platform
----------

If you install Open Media Library on a architecture thats not directly supported,
you need a working python 2.7.x installation and the following packages:

 apt-get install \
    python-pypdf python-stdnum python-html5lib python-chardet python-openssl \
    python-simplejson python-lxml
 pip install -r requirements.txt

On Linux you need to always install:

 apt-get install \
    python-imaging  python-lxml ghostscript

Development
-----------

    mkdir client
    cd client
    git clone https://git.0x2620.org/openmedialibrary.git
    git clone https://git.0x2620.org/openmedialibrary_platform.git platform
    ln -s openmedialibrary/ctl ctl
    ./ctl update_static
    ./ctl db upgrade
    ./ctl setup

    # and start it
    ./ctl debug