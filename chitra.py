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
import os
#from subprocess import call
import subprocess

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames, docURL
from configChitra import settings, adminEmail

def debug(message):
    print message


def first_day_of_month(d):
    return date(d.year, d.month, 1)

def divide_safe(a,  b):
    if b == 0:
        return a
    else:
        return a / b

# Send an email to $address with $content as attachment
# dateUntil is for inclusion in subject line and body message
def send_email(redmineLogin, content, dateUntil):
    msg="Banque pour les makers " + dateUntil.strftime('%Y-%m-%d')



    emailAddress = None
    attachmentPathPart = None

    if redmineLogin == ':admin':
        emailAddress = adminEmail
        attachmentPathPart = 'admin'
    else:
        sql = "select mail from users where login = '%s'" % (redmineLogin)
        sys.stderr.write(sql)
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute(sql)

        emailAddress = cursor.fetchone()
        emailAddress = emailAddress[0]

        attachmentPathPart = emailAddress



    #For using subprocess.calls, see
    #https://stackoverflow.com/questions/89228/calling-an-external-command-in-python
    #https://docs.python.org/3/library/subprocess.html#module-subprocess
    #https://www.pythonforbeginners.com/os/subprocess-for-system-administrators
    #echo $msg  | mutt -a $output -s "$msg" -- "$address"

    dataAttachmentContent = content
    dataAttachmentPath    = os.path.expanduser('~/banque-' + emailAddress + '.csv')
    dataAttachmentFile    = open(dataAttachmentPath, 'w+')
    dataAttachmentFile.write(dataAttachmentContent)
    dataAttachmentFile.close()

    msg = "'" + msg + "'"
    command = 'echo ' + msg + '| mutt -a ' +  dataAttachmentPath + ' -s ' +  msg + ' -- ' + emailAddress
    #call([command])
    print command
    m1 = subprocess.Popen(command, shell=True)
    m1.communicate()


def main():
    # print the connection string we will use to connect
    #debug("Connecting to database...")

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    #debug("Connected!\n")


    dateUntil = first_day_of_month(datetime.datetime.now())
    if sys.argv[1:]:
        dateUntil = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        dateUntil = dateUntil.date()

    legend = ("Positive bank means maker ahead.  Negative means maker owes hours.\n"
              "All units in hours\n"
              "The bank is calculated as bank = hoursSince - (hoursShouldHaveSince - bankAtStart)\n"
              "Hours counted are until %s exclusively\n" % dateUntil.strftime('%Y-%m-%d')
    )


    bankTableForAdmin = ''
    noticeTableForAdmin = ''
    bankTableHeader = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ("Client", "Maker", "Bank", "Since",  "Work done since", "Work should have done since", "Bank at start", "Hours worked/week")
    noticeTableHeader = 'Notice for projects ignored or not set'+"\n"
    for user in settings:
        bankTableForUser = ''
        noticeTableForUser = ''
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

            #### Group time stats by top parent project
            allTime = groupByTopParentChitra(allTime, settings[user][client].get('ignore', ()))

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

            # Generate string containing table data

            print '-'
            print hoursShouldHaveSince
            print '-'
            print bank
            print '-'
            bankTableRow = "%s\t%s\t% .2f\t%s\t%.2f\t%.2f\t%.2f\t%.1f\n" % (client, user, hoursSince - (hoursShouldHaveSince - bank), since, hoursSince, hoursShouldHaveSince, bank, divide_safe(hoursSince, weeksSince))
            bankTableForUser  = bankTableForUser + bankTableRow
            bankTableForAdmin = bankTableForAdmin + bankTableRow


            if settings[user][client].get('ignore'):
                noticeTableRow = "%s\t%s\t%s\n" % (user, "Ignored", "\t".join(settings[user][client]['ignore']))
                noticeTableForUser += noticeTableRow
                noticeTableForAdmin += noticeTableRow

        nonCheckedClients = list(allClients - checkedClients)
        if nonCheckedClients:
            noticeTableRow = "%s\t%s\t%s\n" % (user, "Not set", "\t".join(nonCheckedClients))
            noticeTableForUser += noticeTableRow
            noticeTableForAdmin += noticeTableRow


        # Prepare email to user
        emailContent  = bankTableHeader
        emailContent += "\n".join(sorted(bankTableForUser.split("\n"))) + "\n\n"
        emailContent += noticeTableForUser

        print '=== Doing user ' + user + ' ' + ('=' * 72)
        print emailContent

        # At this point you should email someone
        send_email(user, emailContent, dateUntil)




    # At this point you should email admin
    # Prepare email to user
    emailContent  = bankTableHeader
    emailContent += "\n".join(sorted(bankTableForAdmin.split("\n"))) + "\n\n"
    emailContent += noticeTableForAdmin

    # At this point you should email someone
    send_email(':admin', emailContent, dateUntil)




    return



if __name__ == "__main__":
    main()


