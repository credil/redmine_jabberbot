#!/usr/bin/python2.7
from __future__ import division
from datetime import datetime, date , timedelta
import logging
import pprint
import psycopg2
import sys
import time;
import datetime
from redmine_stats import buildTopParentMap, groupByTopParentChitra;

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames, docURL
from configChitra import settings

def debug(message):
    print message


def first_day_of_month(d):
    return date(d.year, d.month, 1)

def main():
    # print the connection string we will use to connect
    #debug("Connecting to database...")

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    #debug("Connected!\n")


    noticeTable = 'Notice for projects ignored or not set'+"\n"
    dateUntil = first_day_of_month(datetime.datetime.now())
    if sys.argv[1:]:
        dateUntil = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        dateUntil = dateUntil.date()

    bankTable = "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ("Maker", "Client", "Bank", "Since",  "Work done since", "Work should have done since", "Bank at start")
    for user in settings:
        allClients   = set()
        checkedClients      = set()

        for client, config in settings[user].items():
            dateSince = settings[user][client]["since"].strftime('%Y-%m-%d')

            ### We gather this inside the loop because dateSince varies on a per client basis
            sql = """
            select p.identifier, p.id, sum(te.hours) as s, min(spent_on)
            from time_entries te, projects p, users u
                where u.id = te.user_id
                  and te.project_id = p.id
                  and u.login = '%s'
                  and p.status != 5
                  and te.spent_on between '%s' and '%s'
                group by u.login, p.identifier, p.id; """ % (user, dateSince, dateUntil.strftime('%Y-%m-%d'))

            sys.stderr.write(sql)

            cursor.execute(sql)
            allTime = cursor.fetchall()

            allTime = groupByTopParentChitra(allTime, settings[user][client]['ignore'])

            bank        = config["bank"]
            since       = config['since']

            ### This should represent the number of days since start, excluding today
            daysSince       = (dateUntil - since).days
            weeksSince      = daysSince / 7
            hoursPerWeek    = config['hoursPerWeek']
            hoursShouldHaveSince = hoursPerWeek * weeksSince
            hoursSince      = 0
            if client in allTime:
                hoursSince = allTime[client]['hours']

            checkedClients.add(client)
            for key, row in allTime.items():
                allClients.add(key)

            bankTable = bankTable + "%s\t%s\t% .2f\t%s\t%.2f\t%.2f\t%.2f\n" % (user, client, hoursSince - (hoursShouldHaveSince - bank), since, hoursSince, hoursShouldHaveSince, bank)


            if settings[user][client]['ignore']:
                noticeTable = noticeTable + "%s\t%s\t%s\n" % (user, "Ignored", "\t".join(settings[user][client]['ignore']))

        nonCheckedClients = list(allClients - checkedClients)
        if nonCheckedClients:
            noticeTable = noticeTable + "%s\t%s\t%s\n" % (user, "Not set", "\t".join(nonCheckedClients))

    print bankTable
    print
    print noticeTable

    print "Positive bank means maker ahead.  Negative means maker owes hours."
    print "All units in hours"
    print "The bank is calculated as bank = hoursSince - (hoursShouldHaveSince - bankAtStart)"
    print "Hours counted are until %s exclusively" % dateUntil.strftime('%Y-%m-%d')




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

