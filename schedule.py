import sys
import json
from datetime import date
from datetime import datetime
from datetime import timedelta
from monthdelta import monthdelta

# Get CPS payment schedule into a dictionary (map).
# Schedule format is: 'due from date', 'due to date', 'process date'
processing_days = {}
f1 = open('processing_days.csv', 'r')
for line in f1:
    l = line[:-1].split(',')
    processing_days[l[0]] = (l[1], l[2])

# Assuming last processing was yesterday, work out whether
# any payments should be processed today
cps_format = '%d-%b-%Y' # e.g. 24-Jan-2018
now = datetime.now()
itr_date = now
todays_date = now.strftime(cps_format)
process_to_due_date = None
while True:
    k = itr_date.strftime(cps_format)  # create the key to lookup day
    if k in processing_days:            # lookup day in processing days
        # check if payments due on day k should be processed today
        if processing_days[k][1] == todays_date:
            tmp = datetime.strptime(processing_days[k][0], cps_format)
            if (not process_to_due_date or process_to_due_date < tmp):
                process_to_due_date = dt
        else:
            dt = datetime.strptime(processing_days[k][1], date_format)
            # if the new process date is in the future, then we are done today
            if dt > now:
                break
        itr_date = itr_date + timedelta(days=1)
    else:   # something wrong if we can't find the date in our processing days
        break

# If payments should be processed today then process_to_due_date will be set
if not process_to_due_date:
    print('Not a processing day, can not continue')
    sys.exit()

# We now process all payments due up to and including process_to_due_date
print('Processing up to: ' + process_to_due_date.strftime(date_format))
data = json.load(open('schedules.json'))
for schedule in data['schedules']:
    freq_period = schedule['frequency'][1:].upper()
    freq_number = int(schedule['frequency'][0:1])
    if freq_period == 'W':
        delta = timedelta(days=(7 * freq_number))
        print(str(delta))
    elif freq_period == 'M':
        delta = monthdelta(freq_number)
    else:
        continue    # not a valid schedule frequency
    print(schedule['processedUpTo'] + ':' + schedule['frequency'])
