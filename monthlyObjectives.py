#!/usr/bin/python2.7
from jabberbot import JabberBot, botcmd
from datetime import datetime
from datetime import date
import logging
import psycopg2
import sys
import time;

from config import username, password, chatroom, adminuser, ignoreUsers, xmppHandles, userConfig, conn_string, firstNames
from configMonthly import monthly

class SystemInfoJabberBot(JabberBot):
    @botcmd
    def whoami(self, mess, args):
        """Tells you your username"""
        return mess.getFrom().getStripped()


def debug(message):
    print message
    #bot.send(adminuser, message)

# count buisness days from beginning to untilDay inclusively
def calcBuisnessDays(untilDay=31):
    now = datetime.now()
    #holidays = [datetime.date(2013, 8, 14)] # you can add more here
    holidays = [] # you can add more here
    businessdays = 0
    for i in range(1, untilDay +1):
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

	return nowHour-beginHour / (endHour - beginHour)


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

        cursor.execute(sql, (user))
        dataForMonth = cursor.fetchall()

	#Build a hash from that
	hoursWorkedThisMonth = {}
	for row in dataForMonth:
		print "%s: %f" % row[0], row[1]
		hoursWorkedThisMonth[row[0]] = float(row[1])
	print "Done dataForMonth"

	buisnessDays		= calcBuisnessDays(datetime.now().day)
	buisnessDaysTotal	= calcBuisnessDays()


################################################################################

	allProjects = data.keys()
	allProjects.append(hoursWorkedThisMonth.keys())
		

	# For each project
	expectedMonth = {}; deltaTodayForMonth = {};
	debug("For user %s (Hours worked this month / Exepected until end of day today (delta): " % user)
	debug("Postive delta: maker is ahead of hours expected")
	debug("Negative delta: maker needs to do this many hours today to keep estimate at end of month on expected target")
	for(project, hoursPerWeekExpected) in data.items():
		
		#Calulate expected for 28 days: (I actually don't care about last 28 days, so not doing it)
		#But keeping the code in case I change my mind
		#expected28[user][project] = hoursPerWeekExpected*(27+fraction)/5

		#Calulate expected from beginning of month to today, end of day:
		expectedMonth[project] = hoursPerWeekExpected*(buisnessDays+dayFraction())/5
		
		#Calculate the deltas
		deltaTodayForMonth[project] = expectedMonth[project] - hoursWorkedThisMonth[project]

		
		#Generate the delta report
		reportStr = "%.1f / %.1f (%.1f)" % hoursWorkedThisMonth[project], expectedMonth[project], hoursWorkedThisMonth[project] - expectedMonth[project]


if __name__ == "__main__":
    main()

