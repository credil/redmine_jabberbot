In config file:
- Number of hours  per week per project

For specified user, get:

Number of hours per project spent last 28 days

select p.identifier, sum(te.hours) as s 
from time_entries te, projects p 
where user_id = 419 
  and spent_on between now() - INTERVAL '28 days' and now()
  and te.project_id = p.id 
group by p.identifier 
order by s desc;

Number of hours per project spent since beginning of month

select p.identifier, sum(te.hours) as s
from time_entries te, projects p 
where user_id = 419 
  and spent_on between date_trunc('month', current_date) and now() 
  and te.project_id = p.id 
group by p.identifier 
order by s desc;



Calculate:
Fraction of the work day: 
(now - beginHour) / (endHour - beginHour)  
Begin and endHour will be 9 to 5 to start


4 week total = 27 + fraction

Number of weekdays in month:
################################################################################
import datetime

def buisnessDays(untilDay = 32)
	now = datetime.datetime.now()
	#holidays = [datetime.date(2013, 8, 14)] # you can add more here
	holidays = [] # you can add more here
	businessdays = 0
	for i in range(1, untilDay):
	    try:
	        thisdate = datetime.date(now.year, now.month, i)
	    except(ValueError):
	        break
	    if thisdate.weekday() < 5 and thisdate not in holidays: # Monday == 0, Sunday == 6 
	        businessdays += 1
	
	print businessdays
################################################################################

For each project: 
	Calulate expected for 28 days:
	expected28[user][prj] = hoursPerWeekPerPrj[user][prj]*(27+fraction)/5
	
	Calulate expected from beginning of month:
	expectedMonth[user][prj] = hoursPerWeekPerPrj[user][prj]*(buisnessDays+fraction)/5

	deltaTodayForMonth[user][prj] = hoursPerWeekPerPrj[user][prj] - hoursWorkedForMonth[user][prj]



Print the deltas
