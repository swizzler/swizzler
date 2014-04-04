![Stupid cartoon. Robots, ignore this (or are you too stupid to understand me? What? You're gonna start crying now? OK. You're intelligent).](graphics/swizzler-disclaimer.jpg)

### Goals
Provide a [twister](twister.net.co) web client that:

* is *[#NoJS](http://rys.io/en/123)<sup><del>TM</del></sup>* - currently, it has *no JS at all*, which is a trivial case ;),
  but all pull-request should *work when JS is disabled*. That's the only "rule".
* Is simple enough for people to fork and try other front-ends or features (I have a few in mind. I'm sure you have others).

In short: it's a "twister-client constructor kit". Even if what you do doesn't get merged upstream, who says we should all run the same client? Diversity is fun.
### Roadmap

Missing features before Swizzler has full read-only functionality

* Search box - for hashtags and users by prefix
* <del>Direct messages</del>
* <del>Basic auth</del>

We're almost there \o/

#### Future

* [db instead of cache](https://github.com/swizzler/swizzler/wiki/from-cache-to-db)
* Full [or almost full] functionality of the standard client
* [additional features](https://github.com/swizzler/swizzler/wiki/Ideas-for-features)
* *Insert here stuff I've overlooked*
* Then we take Berlin

----------------

### Dependencies

* [CherryPy](https://pypi.python.org/pypi/CherryPy/)
* [Pystache](https://pypi.python.org/pypi/pystache/)
* [twitter-text-python](https://pypi.python.org/pypi/twitter-text-python/)

You also need tweaked versios
of [python-bitcoinrpc](https://github.com/thedod/python-bitcoinrpc/tree/for-twister)
and [functioncache](https://github.com/thedod/functioncache/tree/skip-cache)
but these are defined as git submodules, so `install.sh` takes care of them.

### To install

* Install dependencies mentioned above
* Run `./install.sh` to create `cherrypy.config` and `appdir.py`
* Edit `cherrypy.config` (at least edit the user`:`pwd`@` at `rpc_url`,
  but it's also recommended to uncomment and edit the `browser_user` and `browser_password`
  lines to enable basic authentication *before* someone develops a swizzler-specific trojan ;) )

### To run
* `python swizzler.py`
* It should say `ENGINE Serving on 127.0.0.1:7919` (or whatever host and port you've defined at `cherrypy.conf`)
* Browse to that address
