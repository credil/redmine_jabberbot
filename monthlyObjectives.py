#!/usr/bin/python2.7
from jabberbot import JabberBot, botcmd
from datetime import datetime, date , timedelta
import logging
import pprint
import psycopg2
import sys
import time;

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames, docURL
from configMonthly import monthly

class SystemInfoJabberBot(JabberBot):
    @botcmd
    def whoami(self, mess, args):
        """Tells you your username"""
        return mess.getFrom().getStripped()


def debug(message):
    print message
    #bot.send(adminuser, message)

def notify(redmineUser, message):
	host = username.split('@')[1]

	xmppUser = ''
	if redmineUser in xmppHandles:
       		xmppUser = xmppHandles[redmineUser] + '@' + host


	#debug("Trying to notify {0} : {1}".format(xmppUser, message))
	bot.send(xmppUser, message)
	time.sleep(1)

# count buisness days from fromDay to untilDay inclusively
def calcBuisnessDays(fromDay=1, untilDay=31):
    now = datetime.now()
    #holidays = [datetime.date(2013, 8, 14)] # you can add more here
    holidays = [] # you can add more here
    businessdays = 0
    for i in range(fromDay, untilDay +1):
        try:
            thisdate = date(now.year, now.month, i)
        except(ValueError):
            break
        if thisdate.weekday() < 5 and thisdate not in holidays: # Monday == 0, Sunday == 6 
            businessdays += 1
    
    return businessdays


def dayFraction(beginHour = 9, endHour = 17):

	currentSecond= datetime.now().second
        currentMinute = datetime.now().minute
        currentHour = datetime.now().hour

	nowHour = currentHour + currentMinute/60 + currentSecond/(60*60)

	return (nowHour-beginHour) / (endHour - beginHour)


root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


bot = SystemInfoJabberBot(username,password)
debug('Hello Julien, je suis connecte')


def main():
    # print the connection string we will use to connect
    debug("Connecting to database...")
 
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    debug("Connected!\n")

    for (user, data) in monthly.items():

        # Number of hours per project spent last 28 days
	debug("Doing %s..." % user)
        sql = """select p.identifier, sum(te.hours) as s 
    	from time_entries te, projects p, users u 
    	    where u.login = '%s' 
    	      and u.id = te.user_id 
    	      and spent_on between now() - INTERVAL '28 days' and now() 
    	      and te.project_id = p.id 
    	    group by p.identifier 
    	    order by s desc;""" % user
    
        cursor.execute(sql)
        #cursor.execute(sql)
        data28days = cursor.fetchall()


	#Number of hours per project spent since beginning of month
	sql = ("select p.identifier, sum(te.hours) as s from time_entries te, projects p, users u "
        "where u.login = 'jlam' and u.id = te.user_id  "
        "  and spent_on between date_trunc('month', current_date) and now() "
        "  and te.project_id = p.id "
        "group by p.identifier "
        "order by s desc; ")

	sql = ("select p.identifier, sum(te.hours) as month, "\
	"sum(case when spent_on = current_date then te.hours else 0 end) as today, "\
	"max(te.updated_on) as s "\
	"from time_entries te, projects p, users u "\
	"where u.login = 'jlam' and u.id = te.user_id "\
	"  and spent_on between date_trunc('month', current_date) and now()   "\
	"  and te.project_id = p.id "\
	"group by p.identifier "\
	"order by s desc ")

	print sql

        cursor.execute(sql, (user))
        dataForMonth = cursor.fetchall()

	#Build a hash from that
	hoursWorked = {}
	for row in dataForMonth:
		hoursWorked[row[0]] = {'month' : float(row[1]), 'today' : float(row[2]), 'lastEntry' : row[3]}

	buisnessDays		= calcBuisnessDays(1, datetime.now().day)
	buisnessDaysTotal	= calcBuisnessDays()
	buisnessDaysRemaining	= calcBuisnessDays(datetime.now().day, 32)



	allProjects = data.keys()
	allProjects.append(hoursWorked.keys())
		

	# For each project
	expectedMonth = {}; deltaTodayForMonth = {};
	notify(user, "%s, your hours for this month so far today" % user)
	#notify(user, "For user %s (Hours worked this month / Exepected until end of day today (delta): " % user)
	#notify(user, "For deltas >0: maker is ahead of hours expected; <0: maker needs to do this many hours today to keep end of month estimates on expected target")
	for(project, hoursPerWeekExpected) in data.items():
		
		### Calulate expected for 28 days: 
		# (I actually don't care about last 28 days, so not doing it)
		# But keeping the code in case I change my mind
		#expected28[user][project] = hoursPerWeekExpected*(27+fraction)/5

		#Calulate expected from beginning of month to today, end of day:
		expectedMonthUntilEndOfDay = hoursPerWeekExpected*(buisnessDays)/5
		
		#Generate the delta report
		delta = hoursWorked[project]['month'] - expectedMonthUntilEndOfDay
		deltaSpreadOut = (float(hoursPerWeekExpected) / 5) - ((float(delta) - float(hoursWorked[project]['today'])) / float(buisnessDaysRemaining))

		remainingToday = float(deltaSpreadOut) - float(hoursWorked[project]['today'])

		lastEntry = hoursWorked[project]['lastEntry']
		if lastEntry.date() < datetime.today().date():
			lastEntry = datetime.now()
		eta = lastEntry  + timedelta(hours=remainingToday)
		#print hoursWorked[project]['lastEntry'], remainingToday, eta

		reportStr = "{:s}: {:.1f}, {:.1f}, {:.1f}, {:.1f}, {:.1f}, {:%H:%m}".format(project, hoursWorked[project]['month'], expectedMonthUntilEndOfDay, delta, deltaSpreadOut, remainingToday, eta)
		notify(user, reportStr) 

	notify(user, "See %s for documentation" % docURL)
	notify(user, "Bye\n")


if __name__ == "__main__":
    main()

