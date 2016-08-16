# redmine_jabberbot

Redmine Jabberbot looks at the time entires tables and nags users for not entering their time

Per user customizable thresholds as well.  The bot is configured to nag in a XMPP chatroom so everyone can see, but can report debug messages to one user.

<pre>
(14:06:00) credilbot: metalman, bubbleman, flashman have not logged time in the last 4 hours
</pre>


# monthlyObjectives

monthlyObjectives messages a user privately to give the number of hours needed to bill today to reach a monthly objectives.  See doc/monthlyOjbectives.md .

# chitra

Chitra is keeping tabs on hour banks.  Calculates number of hours billed since a specified begin date and calculates if the redmine user is ahead or behind.
