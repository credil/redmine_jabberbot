#!/usr/bin/python2.7
from datetime import datetime, date , timedelta
import logging
import pprint
import psycopg2
import sys
import time;

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames, docURL
from config

def debug(message):
    print message

def main():
    # print the connection string we will use to connect
    debug("Connecting to database...")
 
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    debug("Connected!\n")
        
    
    # Number of hours per project spent since the beginning of time
    sql = """select u.login, p.identifier, p.id, p.parent_id, sum(te.hours) as s, min(spent_on)
	from time_entries te, projects p, users u 
    	where u.id = te.user_id 
    	  and te.project_id = p.id 
    	group by u.login, p.identifier, p.id, parent_id;""" 
    
    cursor.execute(sql)
    #cursor.execute(sql)
    allTime = cursor.fetchall()

    for row in allTime:
	print row
	#print "%s, %s, %d, %d, %f, %s" % (row[0], row['identifier'], row['id'], row['parent_id'], row['hours'], row['spent_on'])


    exit
    
    
if __name__ == "__main__":
    main()

