# -*- coding: utf-8 -*-
import cherrypy, pystache
from twister import Twister
from appdir import APPDIR

stache = pystache.Renderer(
    search_dirs='{0}/templates'.format(APPDIR),file_encoding='utf-8',string_encoding='utf-8',file_extension='html')

### twistparser (format users, urls, etc. in text). Subclasses twitter-text-python

from ttp import ttp
class TwistParser(ttp.Parser):
    def format_tag(self, tag, text):
        '''Return formatted HTML for a hashtag.'''
        return '<a href="/tag/{0}">{1}{2}</a>'.format(
            ttp.urllib.quote(text.lower().encode('utf-8')), tag, text)

    def format_username(self, at_char, user):
        '''Return formatted HTML for a username.'''
        return '<a href="/user/{0}">{1}{2}</a>'.format(
               user, at_char, user.lower())

    def format_list(self, at_char, user, list_name):
        '''We don't have lists, so we see it as @user followed /something'''
        return '<a href="/user/{0}">{1}{2}</a>/{3}'.format(
               user, at_char, user.lower(), list_name)

    def format_url(self, url, text):
        '''Return formatted HTML for a url.'''
        return '<a target="_blank" rel="nofollow" href="{0}">{1}</a>'.format(ttp.escape(url), text)

twistparser = TwistParser()

def format_twist(message):
    return twistparser.parse(message).html

def format_trending(twister,num_messages=8):
    # ttp would only parse (for example) "#two" in "#two-words". rsplit removes the "-words" (sucks a bit less)
    return [html.rsplit('>',1)[0]+'>' for html in [
        format_twist(u'#{0}'.format(t)) for t in twister.get_trending_tags(num_messages)
    ] if html.find('>')>0] # the if is because ttf doesn't do unicode tags (TODO: find a better ttp fork or find/write some other lib)

### The Swizzler app
class SwizzlerApp(object):
    @cherrypy.expose
    def twist(self,username,k):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        twist = twister.get_twist(username,k)
        rts = twister.get_twist_rts(username,k)
        print rts
        result = {
            'is_twist':True,
            'title':u"@{0}: {1} - Swizzler".format(twist['user']['username'],twist['time']),
            'twist':twist,
            'in_reply_to':twist.get('reply') and twister.get_twist(twist['reply']['user']['username'],twist['reply']['k']) or None,
            'replies':twister.get_twist_replies(username,k),
            'rts':rts,
            'any_rts':not not rts,
            'local_users':twister.local_user_menu()['users'],
            'trending':format_trending(twister,conf['num_messages'])
        }
        return stache.render(stache.load_template('twist'),result)
    @cherrypy.expose
    def user(self,username):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        user = twister.get_user_info(username)
        result = {
            'is_user':True,
            'title':u"{0} (@{1}): Profile - Swizzler".format(user['fullname'],user['username']),
            'subject':user,
            'messages':twister.get_user_posts(username,conf['num_messages']),
            'local_users':twister.local_user_menu()['users'],
            #the filter avoids some utf etc. that ttf can't handle (TODO: fix or replace format_twist)
            'trending':format_trending(twister,conf['num_messages'])
        }
        return stache.render(stache.load_template('standard'),result)
    @cherrypy.expose
    def tag(self,tag):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        result = {
            'is_tag':True,
            'title':u"#{0} - Swizzler".format(tag),
            'subject':{"fullname":tag},
            'messages':twister.get_tag_posts(tag),
            'local_users':twister.local_user_menu()['users'],
            #the filter avoids some utf etc. that ttf can't handle (TODO: fix or replace format_twist)
            'trending':format_trending(twister,conf['num_messages'])
        }
        return stache.render(stache.load_template('standard'),result)
    @cherrypy.expose
    def home(self,localusername,mode='feed'):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        menu = twister.local_user_menu(localusername)
        if mode=='mentions':
            messages = twister.get_user_mentions(localusername)
        else:
            messages = twister.get_user_feed(localusername,conf['num_messages'])
        result = {
            'is_home':True,
            'is_mentions':mode=='mentions',
            'is_feed':mode!='mentions',
            'title':u"{0} (@{1}): Home - Swizzler".format(menu['active']['fullname'],menu['active']['username']),
            'local_users':menu['users'],
            'subject':menu['active'],
            'messages':messages,
            #the filter avoids some utf etc. that ttf can't handle (TODO: fix or replace format_twist)
            'trending':format_trending(twister,conf['num_messages'])
        }
        return stache.render(stache.load_template('standard'),result)
    @cherrypy.expose
    def index(self):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        result = {
            'is_user':True, # i.e. we want to display "bio" and not mentions/DMs/profile buttons
            'title':"Welcome to Swizzler",
            'local_users':twister.local_user_menu('')['users'], # '' means: "Nobody" is active
            'subject':{ # pseudo-user describing sponsored posts
                'fullname':'Sponsored posts',
                'bio':format_twist("""
Mining the twister blockchain protects the #twister-verse from attacks like http://twister.net.co/?p=236
but unlike doge, we don't have shiny coins to offer "our protectors".
Instead, they enjoy occasional minutes of fame in the form of the sponsored posts you see here.
We #Respect their their hard earned crypto-graffiti by appreciating them on coffee/spliff/soy-milk/etc. breaks, because that's how we roll yo.
Start mining today, and all this (AND moral satisfaction) can be yours.""")
            },
            'messages':twister.get_sponsored_posts(conf['num_messages']),
            #the filter avoids some utf etc. that ttf can't handle (TODO: fix or replace format_twist)
            'trending':format_trending(twister,conf['num_messages'])
        }
        return stache.render(stache.load_template('standard'),result)

if __name__ == '__main__':
    cherrypy.config.update('{0}/cherrypy.config'.format(APPDIR))
    app = SwizzlerApp()
    cherrypy.tree.mount(app,'/',config='{0}/cherrypy.config'.format(APPDIR))
    cherrypy.engine.start()
    cherrypy.engine.block()
