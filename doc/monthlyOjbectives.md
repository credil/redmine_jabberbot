# Monthly objectives reports
## Numbers presented

Here is an example of what the script will output:

```
sg1: MTD delta: -5.1 (-7.1); Today: 0.5/4.9 (+0.6); End: 22:04
                 (1)  (2)          (3) (4)  (5)          (6)
```


For each project, the numbers presented are

1. The delta between hours worked this month and expected up to this month at the current time
 * Positive means you are ahead 
 * Negative means you are behind (if it was the end of day)
 * Script assumes start of day at 9:00 and end of day at 18:00
2. The forecasted delta at end of month
2. The hours worked today on that project
3. The number of hours needed to work today to catch up gradually each day
4. The increase in the previous number if you stopped working now with no further time logging for today
5. The estimated time the number of hours will be done, based on no breaks and time of last entry

The script will assume the last time entry is the current time if:
* There were no time entries for that project today
* The last time entry for that project was made 0.83 hours or more before the current time:

At the time of this writing, there are no banks that are taken into account when doing calculations.

## Deltas: positive, negative?
* For a delta >0: the Redmine user is ahead of hours expected;
* For a delta <0: the Redmine user needs do this many hours today to keep end of month estimates on expected target

## FAQ 
### If I did the all the hours for today indicated by the script, why is the delta still negative?

Because it's the number to catch up *gradually*, not to catch up to the total number of hours expected.
