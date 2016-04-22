#!/usr/bin/python2.7

import sys
import time
from datetime import datetime, timedelta

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames, REPL

# import testing_config



if(REPL):
    import threading

    # 'IPython' import to provide the REPL
    try:
        import IPython
    except ImportError:
        print >> sys.stderr, "ipython is not installed....\n\tsudo pip install IPython"

    # create thread for ipython repl if set
    def repl_start():
        IPython.embed()

    th = threading.Thread( target = repl_start )

# 'jabberbot' import
try:
    from jabberbot import JabberBot, botcmd
except ImportError:
    print >> sys.stderr, "you need to install jabberbot...\n\tsudo pip install jabberbot"
    sys.exit(-1)

# 'schedule' import
try:
    # beh maybe this is better? https://github.com/ahawker/crython
    import schedule # https://github.com/dbader/schedule
except ImportError:
    print >> sys.stderr, "you need to install 'schedule'...\n\tsudo pip install schedule OR https://github.com/dbader/schedule"
    sys.exit(-1)


## other IMPORTS
import config
import redmine_stats



## END IMPORT STUFF ###################################################################################

def working_hours():
    """
    return True if during the working week (8am-6pm)
           False otherwise.
    """
    # where monday == 0, sunday == 6

    hour_start = 14 
    hour_end   = 18
    minute_min = 0
    minute_max = 10

    now=datetime.now()
    if(now.weekday() >= 0 and now.weekday() <= 4
	and now.hour >= hour_start and now.hour <= hour_end
    and now.minute >= minute_min and now.minute < minute_max):
        return True
    else:
        return False


## scheduled jobs #####################################################################################

def hour_log(bot, room):
    """
    pass in the instance of the bot
    room is which room we are sending to. Idea being we might send to multiple rooms.
    """
    if(working_hours()):
        # message = "hello guys did you work today? %s" % datetime.now()
        chatroom = room
        message = redmine_stats.get_hours()

        if(message != -1):
            bot.send(chatroom, message, None, 'groupchat')
        else:
            print "getting stats returned error"



class CredilBot(JabberBot):
    def __init__( self, jid, password, res = None):
        DEBUG=config.DEBUG_LOG
        super( CredilBot, self).__init__( jid, password, res,DEBUG)

        self.users = []
        self.message_queue = []
        self.thread_killed = False
        self.timers = []

        try: # newer version of JabberBot uses muc_join_room
            self.muc_join_room(config.chatroom, config.username.split('@')[0])
        except Exception as e:
            self.join_room(config.chatroom, config.username.split('@')[0])

        # schedule jobs
        schedule.every(10).minutes.do(hour_log, self, config.chatroom)


    @botcmd
    def remindme(self, mess, args):
        """
        let the bot remind user of something at a later time.
        (ex: `remindme in 20 minutes "go talk to Patty about Phoenix project"`
        """
        print mess
        print args
        return "not implemented"



    def idle_proc(self):
        """
        super method, gets called periodically
        """
        schedule.run_pending()  # run scheduled tasks


## setup bot        
print "Connecting....."
credilbot = CredilBot( config.username, config.password)

if __name__ == "__main__":
    hour_log(credilbot, config.chatroom)
    if(config.REPL):
        credilbot.serve_forever(connect_callback = lambda: th.start())
    else:
        credilbot.serve_forever(connect_callback = None)



