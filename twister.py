import time
from bitcoinrpc.authproxy import AuthServiceProxy
from functioncache import functioncache,SkipCache

def timestamp2iso(t):
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t))

class Twister:
    def __init__(self,url='http://change:me@127.0.0.1:28332',formatter=None):
        self.twister = AuthServiceProxy(url)
        self.formatter = formatter
    def _format_message(self,message):
        return self.formatter and self.formatter(message) or message
    def clear_cache(self): #doesn't always work :( Need to figure this out.
        db = self.get_user_info._db # It doesn't matter which method. It's the same handler
        db.setup(self.get_user_info) # It needs the function to locate know which db (module's name)
        db.shelve.clear()
        db.shelve.sync()
    def _format_reply(self,r):
        "gracefully fails if reply is empty"
        return r and {"user":self.get_user_info(r['n']),'username':r['n'],'k':r['k']} or {}
    def _format_post_info(self,p):
        result = {
            "height":p['userpost']['height'],
            "k":p['userpost']['k'],
            "time":timestamp2iso(p['userpost']['time']),
        }
        if p['userpost'].has_key('rt'):
            result.update({
                "message":self._format_message(p['userpost']['rt']['msg']),
                "username":p['userpost']['rt']['n'],
                #"user":self.get_user_info(p['userpost']['rt']['n']), ### too heavy. we do it in an iframe
                "k":p['userpost']['rt']['k'],
                "rt_username":p['userpost']['n'],
                #"rt_user":self.get_user_info(p['userpost']['n']), ### too heavy. we do it in an iframe
                "reply":self._format_reply(p['userpost']['rt'].get('reply',{})),
            })
        else:
            result.update({
                "message":self._format_message(p['userpost']['msg']),
                "username":p['userpost']['n'],
                #"user":self.get_user_info(p['userpost']['n']), ### too heavy. we do it in an iframe
                "k":p['userpost']['k'],
                "reply":self._format_reply(p['userpost'].get('reply',{})),
            })
        return result
    @functioncache(ignore_instance=True) # Cache forever. One day we'll look at our old avatars and remember how stupid we used to be.
    def get_twist(self,username,k):
        p = self.twister.dhtget(username,'post{0}'.format(k),'s')
        if p:
            return self._format_post_info(p[0]['p']['v'])
        raise SkipCache("Twist not found @{0}/{1}".format(username,k),{
            "username":"",
            "user":self.get_user_info('nobody'),
            "k":0, # maybe something needs this
            "lastk":0, # or this
            "message":"Twist not found (maybe it's private?) &#128557;",
            "time":"Never"
        })
    @functioncache(60,ignore_instance=True)
    def get_twist_replies(self,username,k):
        return reversed([self._format_post_info(r['p']['v']) for r in self.twister.dhtget(username,'replies{0}'.format(k),'m')]) # We show them oldest first
    @functioncache(60,ignore_instance=True)
    def get_twist_rts(self,username,k):
        return [self._format_post_info(r['p']['v']) for r in self.twister.dhtget(username,'rts{0}'.format(k),'m')]
    @functioncache(60*15,ignore_instance=True)
    def get_user_info(self,username):
        if username == 'nobody':
            return {"username":"","fullname":"Nobody"} # Username is empty. Easier for mustache.
        result = self.twister.dhtget(username,'profile','s')
        if not result:
            #raise SkipCache("user not found: @{0}".format(username), {"username":username,"fullname":username.capitalize()})
            return {"username":username,"fullname":username.capitalize()}
        user = result[0]['p']['v']
        user['username'] = username # handy
        if not user.get('fullname'): # happens
            user['fullname'] = username.capitalize() # Buddha is in the details
        user['bio']=self._format_message(user.get('bio',''))
        try:
            user['avatar'] = self.twister.dhtget(username,'avatar','s')[0]['p']['v']
            if user['avatar']=='img/genericPerson.png': # ugly patch
                user['avatar'] = None
        except:
            user['avatar'] = None
            #raise SkipCache("couldn't get avatar for @{0}, not caching".format(username),user)
        return user
    @functioncache(60*5,ignore_instance=True)
    def local_user_menu(self,active_user=None):
        users = [{'username':'','fullname':'Nobody','active':active_user==''}]
        if active_user=='':
            active = users[0]
        else:
            active = None
        for u in self.twister.listwalletusers():
            user = self.get_user_info(u)
            if active_user==u:
                user.update({'active':True})
                active = user
            users.append(user)
        return {"users":users,"active":active}
    @functioncache(60*5,ignore_instance=True)
    def get_following(self,localusername):
        return [{"username":u} for u in self.twister.getfollowing(localusername)]
    @functioncache(60*5,ignore_instance=True)
    def get_sponsored_posts(self,num=8):
        return reversed([self._format_post_info(p) for p in self.twister.getspamposts(num)]) # Don't ask me why reversed :)
    @functioncache(60,ignore_instance=True)
    def get_tag_posts(self,tag):
        return [self._format_post_info(p['p']['v']) for p in self.twister.dhtget(tag,'hashtag','m')]
    @functioncache(60,ignore_instance=True)
    def get_user_feed(self,localusername,num=8):
        return [self._format_post_info(p) for p in self.twister.getposts(num,self.get_following(localusername))]
    @functioncache(60,ignore_instance=True)
    def get_user_mentions(self,localusername):
        return [self._format_post_info(p['p']['v']) for p in self.twister.dhtget(localusername,'mention','m')]
    @functioncache(60,ignore_instance=True)
    def get_user_messages(self,localusername,username=None,num=2):
        if username:
            raw = self.twister.getdirectmsgs(localusername,num,[{"username":username}])
        else:
            raw = self.twister.getdirectmsgs(localusername,num,self.get_following(localusername))
        result =[]
        localuser = self.get_user_info(localusername)
        for username in raw:
            user = self.get_user_info(username)
            messages = []
            latest_ts = 0
            for message in raw[username]:
                if message['time'] > latest_ts:
                    latest_ts = message['time']
                message['time'] = timestamp2iso(message['time'])
                message['username'] = message['fromMe'] and localusername or username
                message['user'] = message['fromMe'] and localuser or user
                message['message'] = self._format_message(message['text'])
                messages.insert(0,message) # reverse order (newer first)
            result.append({'username':username,'user':user,'messages':messages,'latest_ts':latest_ts})
        return sorted(result,key=lambda thread:thread['latest_ts'],reverse=True)
                
    @functioncache(60,ignore_instance=True)
    def get_user_posts(self,username,num=8):
        result = [self._format_post_info(p) for p in self.twister.getposts(num,[{'username':username}])]
        if result:
            return result
        else: # We're not following. Let's "knit" the best timeline we can
            result = self.twister.dhtget(username,'status','s')
            while True:
               try:
                   lastk = result[-1]['p']['v']['userpost']['lastk']
                   last = lastk and self.twister.dhtget(username,'post{0}'.format(result[-1]['p']['v']['userpost']['lastk']),'s')
               except:
                   break
               if not last:
                   break 
               result.append(last[0])
            return [self._format_post_info(s['p']['v']) for s in result]
    def get_users_by_partial_name(self,prefix,num=8):
        return self.twister.listusernamespartial(prefix,num)
    @functioncache(60,ignore_instance=True)
    def get_trending_tags(self,num=8):
        return self.twister.gettrendinghashtags(num)
    def get_info(self): # not cached
        return self.twister.getinfo()
