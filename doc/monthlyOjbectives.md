# Monthly objectives reports
## Numbers presented

Here is an example of what the script will output:

```
sg1: MTD delta: -18.6; Today: 0.0/7.1 (+1.0); End: 17:38
                 (1)          (2) (3)  (4)          (5)
```


For each project, the numbers presented are

1. The delta between hours worked this month and expected this month at end of day
 * Positive means you are ahead 
 * Negative means you are behind (if it was the end of day)
2. The hours worked today on that project
3. The number of hours needed to work today to catch up gradually
4. The increase in the previous number if you stopped working now with no further time logging for today
5. The estimated time the number of hours will be done, based on no breaks and time of last entry

The script will assume the last time entry is the current time if:
* There were no time entries for that project today
* The last time entry for that project was made 1.27 hours or more before the current time:

At the time of this writting, there are no banks that are taken into account when doing calculations.

## Deltas: postive, negative?
* For a delta >0: the redmine user is ahead of hours expected; 
* For a delta <0: the redmine user needs do this many hours today to keep end of month estimates on expected target

## FAQ 
### If I did the all the hours for today indicated by the script, why is the delta still negative

Because it's the number to catch up *gradually*, not to catch up to the total number of hours expected.
