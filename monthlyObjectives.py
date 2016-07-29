#!/usr/bin/python2.7
from jabberbot import JabberBot, botcmd
from datetime import datetime, date , timedelta
import logging
import pprint
import psycopg2
import sys
import time;
from redmine_stats import groupByTopParent, lastTimeEntry
import os.path

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

# count business days from fromDay to untilDay inclusively
def calcBuisnessDays(fromDay=1, untilDay=31, calcBuisnessDaysOnly=True):

    if not calcBuisnessDaysOnly:
	return untilDay + 1 - fromDay

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


def dayFraction(beginHour = 9, endHour = 18):

	currentSecond= datetime.now().second
        currentMinute = datetime.now().minute
        currentHour = datetime.now().hour

	nowHour = currentHour + float(currentMinute)/60 + float(currentSecond)/(60*60)
	#debug("%f = %f + %f/60 + %f/(60*60)" % (nowHour, currentHour, currentMinute, currentSecond))

	frac = max(min((float(nowHour)-float(beginHour)) / (float(endHour) - float(beginHour)), 1), 0)

	debug(frac)
	return frac





root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

debug('Python script starting....')

bot = SystemInfoJabberBot(username,password)
debug('Hello Julien, je suis connecte')



"""
Determine if we are within normal updating times
"""
def inAnnounceTime():
    hour_start = 11
    hour_end   = 18
    now=datetime.now()
    if  now.weekday() >= 0 and now.weekday() <= 4 and now.hour >= hour_start and now.hour < hour_end:
        return True
    else:
        return False


### Determine first if there was a new time entry, how old was the last annoucement
### and thus we should report time
def goReport(user):
    lastEntryAtLastPassPath = "/tmp/monthlyObjecttives.%s.lastEntry.txt" % user

    doContinue = False
    doUpdate = False

    lastEntryForUser    = lastTimeEntry(user)
    lastEntryForUserStr = lastEntryForUser.strftime("%Y/%m/%d %H:%M")
    if not os.path.isfile(lastEntryAtLastPassPath):
        doContinue = True
    else:
        content = ''
        with open(lastEntryAtLastPassPath, 'r') as content_file:
                content = content_file.read()

        secsSinceLastEntry  = time.time() - float(lastEntryForUser.strftime("%s"))
        secsSinceLastAnnounce = time.time() - os.path.getmtime(lastEntryAtLastPassPath)

        """
        Update if:
        - A new time entry has been made, at any time
        - If we are in announce time:
          - If it has been at least 6 hours since the last entry and 5 minutes since the last announce
          - If it has been 2 hours since the last announce
        """
        if lastEntryForUserStr != content:
            doContinue = True
        elif inAnnounceTime():
            if (secsSinceLastEntry > 6*60*60 and secsSinceLastAnnounce > 5*60) or secsSinceLastAnnounce > 2*60*60:
                doUpdate = True
                os.utime(lastEntryAtLastPassPath, None)
            else:
                debug("Skipping %s cause last announcement too soon, " % user)
        else:
            debug("Skipping %s cause last entry reported and we are not in announce time, " % user)




    if doContinue:
        f = open(lastEntryAtLastPassPath, 'w')
        f.write(lastEntryForUserStr)
        f.close

    return doContinue or doUpdate


def main():
    # print the connection string we will use to connect
    debug("Connecting to database...")

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    debug("Connected!\n")

    for (user, data) in monthly.items():

        if goReport(user) == False:
            continue


        ### Now continue reporting for that user
    	debug("Doing %s..." % user)
    	##Number of hours per project spent since beginning of month
    	sql = ("select p.id, p.parent_id, p.identifier, sum(te.hours) as month, "\
    	"sum(case when spent_on = current_date then te.hours else 0 end) as today, "\
    	"max(te.updated_on) as s "\
    	"from time_entries te, projects p, users u "\
    	"where u.login = '%s' and u.id = te.user_id "\
    	"  and spent_on between date_trunc('month', current_date) and now()   "\
    	"  and te.project_id = p.id "\
    	"group by p.id, p.identifier, p.parent_id "\
    	"order by s desc ") % user

    	print sql

        cursor.execute(sql, (user))
        dataForMonth = cursor.fetchall()

        dataForMonth = groupByTopParent(dataForMonth)

	#Build a hash from that
	hoursWorked = {}
	for id, row in dataForMonth.items():
		hoursWorked[row['identifier']] = {'month' : float(row['hoursMonth']), 'today' : float(row['hoursToday']), 'lastEntry' : row['lastUpdate']}


	# Calculate date stuff
        now = datetime.now()
	thisdate = date(now.year, now.month, now.day)
	# weekday = thisdate.weekday() < 5
	weekday = True   # Always assume it's a weekday as we want to see the weekday plan on a weekend
	buisnessDays = calcBuisnessDays(1, datetime.now().day, weekday)
	buisnessDaysTotal = calcBuisnessDays(1, 32, weekday)
	buisnessDaysRemaining = max(calcBuisnessDays(datetime.now().day, 32, weekday), 1)
	frac = dayFraction();
	forecastRatio = float(buisnessDaysTotal) / (float(buisnessDays) + float(frac))
	#debug("%.1f = %.1f / (%.1f + %.1f)" % (forecastRatio, buisnessDaysTotal, buisnessDays, frac))


	debug("Doing %s..." % user)

    	allProjects = data.keys()
	allProjects.append(hoursWorked.keys())


	# For each project

	notify(user, "%s, your hours for this month so far today" % user)
	deltaTotal = 0; deltaSpreadOutTotal = 0; remainingTodayTotal = 0;
    	workedTodayTotal = 0; deltaIncreaseTotal = 0; deltaForcastTotal = 0;
	lastEntryMax = date(1, 1, 1); lastEntryMax = datetime.combine(lastEntryMax, datetime.min.time())
	for(project, hoursPerWeekExpected) in data.items():
		if project not in hoursWorked:
			hoursWorked[project] = {'month' : 0, 'today' : 0, 'lastEntry' : datetime.now()}

		### Calulate expected for 28 days:
		# (I actually don't care about last 28 days, so not doing it)
		# But keeping the code in case I change my mind
		#expected28[user][project] = hoursPerWeekExpected*(27+fraction)/weekday

		#Add worked today totals for reporting after the this for loop
		workedTodayTotal += hoursWorked[project]['today']

		#Calulate expected from beginning of month to today, end of day:
		daysPerWeek = 5 if weekday else 7
		expectedMonthUntilNow = hoursPerWeekExpected*float(buisnessDays-1+frac)/daysPerWeek

		#Generate the delta report
		delta        = hoursWorked[project]['month'] - expectedMonthUntilNow
		deltaTotal  += delta

		#Forcast delta at end of month
        	deltaForcast         = delta * forecastRatio
	        deltaForcastTotal   += deltaForcast


		#Delta spread out: if you wanted 0 delta by end of month, how much would
		#you have to work on the remaining business days, including today
		expectedMonthUntilYesterdayEOD = hoursPerWeekExpected*(buisnessDays-1)/daysPerWeek
		expectedEndOfMonth = hoursPerWeekExpected*(float(buisnessDaysTotal))/daysPerWeek
		deltaSpreadOut = (expectedEndOfMonth - (float(hoursWorked[project]['month']) - float(hoursWorked[project]['today'])))/float(buisnessDaysRemaining)
		deltaSpreadOutTotal += deltaSpreadOut

		#Delta increase: If you stopped working now, how much would your delta spread out increase by
		deltaIncrease = (deltaSpreadOut - hoursWorked[project]['today'])/max(buisnessDaysRemaining-1,1)
		deltaIncreaseTotal += deltaIncrease


		remainingToday = float(deltaSpreadOut) - float(hoursWorked[project]['today'])
		remainingTodayTotal += remainingToday

		lastEntry = hoursWorked[project]['lastEntry']
		diff = datetime.now() - lastEntry
		lastEntryMax = max(lastEntryMax, lastEntry)

		# To refresh average time entry,
		# select login, avg(hours) as hours from time_entries te, users u where user_id = u.id and hours between 0 and 6 group by u.login order by hours;
		if lastEntry.date() < datetime.today().date() or diff > timedelta(hours=0.83):
			lastEntry = datetime.now()
		eta = lastEntry  + timedelta(minutes=float(remainingToday)*60)

		# Print with more condensed format
		reportStr = "{:s}: MTD delta: {:.1f} (Frcst: {:.1f}); Today: {:.1f}/{:.1f} ({:+.1f}); End: {:%H:%M}".format(project,  delta, deltaForcast, hoursWorked[project]['today'], deltaSpreadOut, deltaIncrease, eta)
		notify(user, reportStr)

	diff = datetime.now() - lastEntryMax
	if lastEntryMax.date() < datetime.today().date() or diff > timedelta(hours=1.27):
		lastEntryMax = datetime.now()
	eta = lastEntryMax  + timedelta(minutes=float(remainingTodayTotal)*60)
	reportStr = "Total: MTD delta: {:.1f} (Frcst: {:.1f}); Today: {:.1f}/{:.1f} ({:+.1f}); End: {:%H:%M}".format(deltaTotal, deltaForcastTotal, workedTodayTotal, deltaSpreadOutTotal, deltaIncreaseTotal, eta)
	notify(user, reportStr)

	notify(user, "See %s for documentation" % docURL)
	notify(user, "Bye\n")


if __name__ == "__main__":
    main()

