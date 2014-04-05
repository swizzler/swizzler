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
        return '<a href="{0}/tag/{1}">{2}{3}</a>'.format(
            cherrypy.request.base+cherrypy.request.script_name,
            ttp.urllib.quote(text.lower().encode('utf-8'),'xmlcharrefreplace'), tag, text)

    def format_username(self, at_char, user):
        '''Return formatted HTML for a username.'''
        return '<a href="{0}/user/{1}">{2}{3}</a>'.format(
            cherrypy.request.base+cherrypy.request.script_name,
            user, at_char, user.lower())

    def format_list(self, at_char, user, list_name):
        '''We don't have lists, so we see it as "@user" followed by "/something"'''
        return '<a href="{0}/user/{1}">{2}{3}</a>/{4}'.format(
            cherrypy.request.base+cherrypy.request.script_name,
            cherrypy.request.base+cherrypy.request.script_name, user, at_char, user.lower(), list_name)

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
    def _standard_params(self,twister,q,num_items=8):
        result = {'site_root':cherrypy.request.base+cherrypy.request.script_name}
        result['here'] = result['site_root']+cherrypy.request.path_info
        q=(q or '').strip().split(' ')[0] # ignore anything after the first space if any
        if q.startswith('#'): # user said "#sometag", change to "sometag"
            q=q[1:]
        if q and not q.startswith('@'): # Tag. redirect.
            raise cherrypy.HTTPRedirect(result['site_root']+'/tag/{0}'.format(q))
        if q:
            result['user_prefix'] = q
            result['users'] = twister.get_users_by_partial_name(q[1:],num_items)
            return result
        result['trending'] = format_trending(twister,num_items)
        return result
          
    @cherrypy.expose
    def twist(self,username,k,q=None):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        params = self._standard_params(twister,q,conf['num_messages']) # called as soon as possible, because it might raise a redirect
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
            'info':twister.get_info(),
        }
        result.update(params)
        return stache.render(stache.load_template('twist'),result)
    @cherrypy.expose
    def user(self,username,q=None):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        params = self._standard_params(twister,q,conf['num_messages']) # called as soon as possible, because it might raise a redirect
        user = twister.get_user_info(username)
        messages = twister.get_user_posts(username,conf['num_messages'])
        result = {
            'is_user':True,
            'title':u"{fullname} (@{username}): Profile - Swizzler".format(**user),
            'subject':user,
            'messages':messages,
            'any_messages':not not messages,
            'local_users':twister.local_user_menu()['users'],
            'info':twister.get_info(),
        }
        result.update(params)
        return stache.render(stache.load_template('standard'),result)
    @cherrypy.expose
    def tag(self,tag,q=None):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        params = self._standard_params(twister,q,conf['num_messages']) # called as soon as possible, because it might raise a redirect
        messages = twister.get_tag_posts(tag)
        result = {
            'is_tag':True,
            'title':u"#{0} - Swizzler".format(tag),
            'subject':{"fullname":tag},
            'messages':messages,
            'any_messages':not not messages,
            'local_users':twister.local_user_menu()['users'],
            'info':twister.get_info(),
            #the filter avoids some utf etc. that ttf can't handle (TODO: fix or replace format_twist)
        }
        result.update(params)
        return stache.render(stache.load_template('standard'),result)
    @cherrypy.expose
    def home(self,localusername,mode='feed',q=None):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        params = self._standard_params(twister,q,conf['num_messages']) # called as soon as possible, because it might raise a redirect
        menu = twister.local_user_menu(localusername)
        if mode=='mentions':
            messages = twister.get_user_mentions(localusername)
        else:
            messages = twister.get_user_feed(localusername,conf['num_messages'])
        result = {
            'is_home':True,
            'is_mentions':mode=='mentions',
            'is_feed':mode!='mentions',
            'title':u"{fullname} (@{username}): Home - Swizzler".format(**menu['active']),
            'local_users':menu['users'],
            'info':twister.get_info(),
            'subject':menu['active'],
            'messages':messages,
            'any_messages':not not messages,
        }
        result.update(params)
        return stache.render(stache.load_template('standard'),result)
    @cherrypy.expose
    def messages(self,localusername,remoteusername=None,q=None):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        params = self._standard_params(twister,q,conf['num_messages']) # called as soon as possible, because it might raise a redirect
        localuser = twister.get_user_info(localusername)
        remoteuser = remoteusername and twister.get_user_info(remoteusername) or None
        threads = remoteusername and twister.get_user_messages(localusername,remoteusername,conf['num_messages']) or twister.get_user_messages(localusername)
        result = {
            'title':u"{0} (@{1}): direct messages{2}".format(
                localuser['fullname'],localuser['username'],
                remoteuser and u" with {fullname} (@{username}) - Swizzler".format(**remoteuser) or ""),
            'subject':localuser,
            'remoteuser':remoteuser,
            'threads':threads,
            'any_threads':not not threads,
            'local_users':twister.local_user_menu()['users'],
            'info':twister.get_info(),
            #the filter avoids some utf etc. that ttf can't handle (TODO: fix or replace format_twist)
        }
        result.update(params)
        return stache.render(stache.load_template('messages'),result)
    @cherrypy.expose
    def index(self,q=None):
        conf = cherrypy.request.app.config['swizzler']
        twister = Twister(conf['rpc_url'],format_twist)
        params = self._standard_params(twister,q,conf['num_messages']) # called as soon as possible, because it might raise a redirect
        messages = twister.get_sponsored_posts(conf['num_messages'])
        result = {
            'is_user':True, # i.e. we want to display "bio" and not mentions/DMs/profile buttons
            'title':"Welcome to Swizzler",
            'local_users':twister.local_user_menu('')['users'], # '' means: "Nobody" is active
            'info':twister.get_info(),
            'subject':{ # pseudo-user describing sponsored posts
                'fullname':'Sponsored posts',
                'bio':format_twist("""
Mining the twister blockchain protects the #twister-verse from attacks like http://twister.net.co/?p=236
but unlike doge, we don't have shiny coins to offer "our protectors".
Instead, they enjoy occasional minutes of fame in the form of the sponsored posts you see here.
We #Respect their hard earned crypto-graffiti by appreciating them on coffee/spliff/soy-milk/etc. breaks, because that's how we roll yo.
Start mining today, and all this (AND moral satisfaction) can be yours.""")
            },
            'messages':messages,
            'any_messages':not not messages,
            #the filter avoids some utf etc. that ttf can't handle (TODO: fix or replace format_twist)
        }
        result.update(params)
        return stache.render(stache.load_template('standard'),result)

if __name__ == '__main__':
    cherrypy.config.update('{0}/cherrypy.config'.format(APPDIR))
    app = SwizzlerApp()
    cherrypy.tree.mount(app,'/',config='{0}/cherrypy.config'.format(APPDIR))
    conf = cherrypy.tree.apps[''].config
    u,p = conf['swizzler'].get('browser_user'),conf['swizzler'].get('browser_password')
    print u,p
    if u and p:
        conf['/'].update({ 'tools.basic_auth.on': True,
            'tools.basic_auth.realm': 'Swizzler VIP lounge',
            'tools.basic_auth.users': {u:p}, 
            'tools.basic_auth.encrypt': lambda x: x})
    cherrypy.engine.start()
    cherrypy.engine.block()
