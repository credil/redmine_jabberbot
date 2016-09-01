#!/usr/bin/python2.7
import psycopg2
import sys
import time
import datetime

import logging

import sys
import time;

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames

connected = False

def announce(message):
    print message
    # debug('Trying to announce in ' + chatroom + ': ' + message)
    # bot.send(chatroom, message, None, 'groupchat')
    # time.sleep(1)

def debug(message):
    print message
    #bot.send(adminuser, message)


# root = logging.getLogger()
# root.setLevel(logging.DEBUG)

# ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ch.setFormatter(formatter)
# root.addHandler(ch)


#bot = SystemInfoJabberBot(username,password)

#print bot.muc_room_participants(chatroom);


#########
# Expected format: an array of hashes with index
# prjId, dontCare, prjIdetnfier, hoursMonth, hoursToday, lastUpdate
def groupByTopParent(dataForMonth):

    byTopParent = {}
    topParentMap = buildTopParentMap()

    for row in dataForMonth:
       prjId        = row[0]
       #prjParentId  = row[1]
       prjIdentifier= row[2]
       hoursMonth   = row[3]
       hoursToday   = row[4]
       lastUpdate   = row[5]

       topParent = topParentMap[prjId]

       if topParent is None or topParent not in byTopParent:
           paIdentifier = getIdentifier(topParent)
           byTopParent[topParent] = {'identifier': paIdentifier, 'hoursMonth': hoursMonth, 'hoursToday': hoursToday, 'lastUpdate': lastUpdate}
       else:
           byTopParent[topParent]['hoursMonth'] += hoursMonth
           byTopParent[topParent]['hoursToday'] += hoursToday
           byTopParent[topParent]['lastUpdate'] = max(lastUpdate, byTopParent[topParent]['lastUpdate'])

    return byTopParent

def groupByTopParentChitra(dataSums, ignore = None):
    byTopParent = {}
    topParentMap = buildTopParentMap()

    # Format of row is  p.identifier, p.id, sum(te.hours) as s, min(spent_on)
    for row in dataSums:
       prjIdentifier= row[0]
       prjId        = row[1]
       hours        = row[2]
       start        = row[3]

       if any(prjIdentifier in ign for ign in ignore):
           continue

       topParent = topParentMap[prjId]
       paIdentifier = None
       if topParent is not None:
           paIdentifier = getIdentifier(topParent)

       if topParent is None or paIdentifier not in byTopParent:
           byTopParent[paIdentifier] = {'id': topParent, 'hours': hours, 'start': start}
       else:
           oldHours = byTopParent[paIdentifier]['hours']
           newHours = hours + oldHours
           byTopParent[paIdentifier]['hours'] = newHours
           byTopParent[paIdentifier]['start'] = min(start, byTopParent[paIdentifier]['start'])

       #print prjIdentifier, byTopParent, "\n"

    return byTopParent


def lastTimeEntry(user):
    sql = "select max(te.updated_on) from time_entries te, users u where u.login = '%s' and te.user_id = u.id" % user

    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute(sql)
    maxTimeEntry = cursor.fetchone()[0]
    return maxTimeEntry


def getIdentifier(prjId):
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    sql = "select identifier from projects where id = %d" % prjId;
    cursor.execute(sql)
    identifier = cursor.fetchone()[0]
    return identifier





def buildTopParentMap():
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    #debug("Building top parent map...")
    topParentMap = {}
    sql = "select id, parent_id from projects;"
    cursor.execute(sql)
    prjParents = cursor.fetchall()

    for row in prjParents:
        id   = row[0]
        paId = row[1]

        finalParent = None

        # First lets look at ourselve, see if we have a parent
        if paId is None:
            finalParent = id
        else:
            finalParent = paId

        # Lets look at our parent, see if their top parent has been determined
        if paId in topParentMap and topParentMap[paId] is not None:
            finalParent = topParentMap[paId]

        topParentMap[id] = finalParent

        for childId, childParentId in topParentMap.items():
            if childParentId == id:
                topParentMap[childId] = finalParent

    return topParentMap




def get_hours():
    thresholdDefault = 4

    # print the connection string we will use to connect
    debug("Connecting to database...")

    # get a connection, if a connect cannot be made an exception will be raised here
    try:
        conn = psycopg2.connect(conn_string)
    except psycopg2.OperationalError as e:
        debug(e)
        return -1


    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    debug("Connected!\n")

    sql = "select u.login, max(te.updated_on) from time_entries te, users u where u.id = te.user_id and hours > 0 group by u.login order by max(te.updated_on);"

    cursor.execute(sql)
    data = cursor.fetchall()

    # Calculate late users first
    lateUsers = []
    for row in data:
        hoursSinceLastLog = (datetime.datetime.now() - row[1]).total_seconds() / 60 / 60
	debug(str(row) + ' ' + str(hoursSinceLastLog))

	redmineHandle = row[0]

	threshold = thresholdDefault;
	if redmineHandle in userConfig and 'threshold' in userConfig[redmineHandle]:
	    threshold = userConfig[row[0]]['threshold']

	if hoursSinceLastLog > threshold and row[0] not in ignoreUsers:
	    maker = row[0]
            if maker in xmppHandles:
		maker = xmppHandles[maker]
 	    #lateUsers.append(maker + ' (' + str(round(hoursSinceLastLog, 1)) + ' > ' + str(threshold) + ')');
 	    lateUsers.append(maker)


    # Calculate total hours
    sql = "select u.login, sum(hours), min(spent_on) from time_entries te, users u where u.id = te.user_id and te.spent_on >= now() - INTERVAL '7 days' and te.spent_on <= now() group by u.login order by sum(hours);"

    cursor.execute(sql)
    data = cursor.fetchall()

    hoursLoggedStr = ''
    dateMin = datetime.date.max
    rosterCheck = dict(firstNames)
    spaceStr = '   '
    for row in data:
	if (row[2] < dateMin):
		dateMin = row[2]

	maker = row[0]
        if maker in firstNames:
	    del rosterCheck[maker]
	    maker = firstNames[maker]


	hoursLoggedStr += maker + ': ' + str(round(row[1], 1))  + spaceStr

    for firstName in rosterCheck:
	hoursLoggedStr = firstName + ': 0' + spaceStr + hoursLoggedStr

    hoursLoggedStr += '(since ' + str(dateMin) + ')\n'


    # Calculate hours per project, last 28 days
    sql = "select u.login, sum(hours), min(spent_on) from time_entries te, users u where u.id = te.user_id and te.spent_on >= now() - INTERVAL '28 days' group by u.login order by sum(hours);"

    cursor.execute(sql)
    data = cursor.fetchall()

    hoursLast28days = ''
    for row in data:
	maker = row[0]
        if maker in firstNames:
	    maker = firstNames[maker]

	hoursLast28days += maker + ': ' + str(row[1]) + ' (since ' + str(row[2]) + ')\n'




    # Now for the annoucements
    # bot.join_room(chatroom, 'credilbot')
    # time.sleep(1)
    return_string = ""
    if lateUsers:
        return_string += ', '.join(lateUsers) + ' have not logged time within their set threshold (default '+ str(thresholdDefault) +' hours)'
    else:
        return_string += 'Congrats everyone for logging your hours today!!!'
    return_string += '\n'

	# announce(', '.join(lateUsers) + ' have not logged time within their set threshold (default '+ str(thresholdDefault) +')')

    return_string +='Total numbers of hours logged in last 7 days\n'
    # announce('Total numbers of hours logged in last 7 days')
    return_string += hoursLoggedStr
    # announce(hoursLoggedStr)
    return return_string




if __name__ == "__main__":
    ret =  get_hours()
    print "\n\n"
    print ret
    # main()

