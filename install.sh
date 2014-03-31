#!/bin/sh
# Note: python-bitcoinrpc and functioncache are twister-specific branches
# Perhaps their pull-requests will get merged upstream one day (and we'll rebase when it happens)
# but we can't let it stop us :)
git submodule update --init
if [ -f cherrypy.config ] ; then
    echo you already have cherrypy.config
else
    sed -e "s:/PATH/HERE:`pwd`:" \
        -e "s/RANDOM/$(python -c "import random; print random._urandom(60).encode('base_64').strip().replace('\n','').replace('/','')")/" \
        < cherrypy.config.example > cherrypy.config
    echo "created cherrypy.config. Now edit it to taste ;)"
fi
