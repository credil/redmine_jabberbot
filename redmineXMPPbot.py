from jabberbot import JabberBot, botcmd
import datetime
import logging
import psycopg2
import sys
import time;

from config import username, password, chatroom, adminuser

class SystemInfoJabberBot(JabberBot):
    @botcmd
    def serverinfo( self, mess, args):
        """Displays information about the server"""
        version = open('/proc/version').read().strip()
        loadavg = open('/proc/loadavg').read().strip()

        return '%snn%s' % ( version, loadavg, )

    @botcmd
    def time( self, mess, args):
        """Displays current server time"""
        return str(datetime.datetime.now())

    @botcmd
    def rot13( self, mess, args):
        """Returns passed arguments rot13'ed"""
        return args.encode('rot13')

    @botcmd
    def whoami(self, mess, args):
        """Tells you your username"""
        return mess.getFrom().getStripped()


root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


bot = SystemInfoJabberBot(username,password)
bot.join_room(chatroom, 'credilbot')
debug('Hello Julien, je suis connecte')
#print bot.muc_room_participants(chatroom);
announce('Testing...') 


def main():
    #Define our connection string
    conn_string = "host='localhost' dbname='redmine' user='redmine' password='credil_007'"
 
    # print the connection string we will use to connect
    debug("Connecting to database\n ->%s" % (conn_string))
 
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    debug("Connected!\n")
 
if __name__ == "__main__":
    main()

while 1: 
	debug(str(datetime.datetime.now()))
	time.sleep(5)


def announce(message)
    print message
    bot.send(chatroom, message, None, 'groupchat')
    
def debug(message)
    print message
    bot.send(adminuser, message)

bot.serve_forever()
