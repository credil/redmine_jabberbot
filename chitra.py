#!/usr/bin/python2.7
from datetime import datetime, date , timedelta
import logging
import pprint
import psycopg2
import sys
import time;

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames, docURL
from configChitra import settings

def debug(message):
    print message

def buildTopParent():
    sql = """WITH RECURSIVE Ancestors AS (
   	SELECT id, parent_id, 0 AS level FROM projects WHERE parent_id IS NULL
	   UNION ALL
	SELECT child.id, child.parent_id, level+1 
	   FROM projects child 
	       INNER JOIN Ancestors p ON p.id=child.parent_id
	)
	SELECT p.id, a.parent_id, a.level 
		FROM Ancestors a
		INNER JOIN Projects p ON p.id = a.id
	;"""
    cursor.execute(sql)
    allProjects = cursor.fetchall()

    

def main():
    # print the connection string we will use to connect
    debug("Connecting to database...")
 
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    debug("Connected!\n")


    allProjects = buildTopParent

    for user in settings:
	for client in settings[user]:
		dateSince = settings[user][client]["since"].strftime('%Y-%m-%d')
    		sql = """select u.login, p.identifier, p.id, p.parent_id, sum(te.hours) as s, min(spent_on)
			from time_entries te, projects p, users u 
		    	where u.id = te.user_id 
	    		  and te.project_id = p.id 
			  and u.login = '%s'
			  and p.status != 5
			  and te.spent_on >= '%s'
	    		group by u.login, p.identifier, p.id, parent_id;""" % (user, dateSince)
    
		cursor.execute(sql)
    		#cursor.execute(sql)
    		allTime = cursor.fetchall()

		for row in allTime:
			print row
			#print "%s, %s, %d, %d, %f, %s" % (row[0], row['identifier'], row['id'], row['parent_id'], row['hours'], row['spent_on'])




        
    return
    
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


    

if __name__ == "__main__":
    main()

