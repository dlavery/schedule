import sys
import json
from datetime import date
from datetime import datetime
from datetime import timedelta
from monthdelta import monthdelta

##########################################
# FUNCTIONS
##########################################
# Create a CPS format string from a date
def formet_as_cps_date(d):
    if d:
        return d.strftime('%d-%b-%Y') # e.g. 24-Jan-2018
    else:
        return ''

# Create a date from a CPS format string
def date_from_cps_format(cps):
    if cps:
        return datetime.strptime(cps, '%d-%b-%Y')
    else:
        return ''

# Create an ISO date format string from a date
def format_as_iso_date(d):
    if d:
        return d.strftime('%Y-%m-%d')
    else:
        return ''

# Create a date from an ISO format string
def date_from_iso_format(iso):
    if iso:
        return datetime.strptime(iso,'%Y-%m-%d')
    else:
        return ''

# Make a payment
def make_payment(schedule, reference):
    print('PAYMENT: '
    + schedule['payee']['name'] + '|'
    + schedule['payee']['sortCode'] + '|'
    + schedule['payee']['account'] + '|'
    + reference + '|'
    + str('%.2f' % schedule['amount']))


##########################################
# MAIN SCRIPT
##########################################
# Get CPS payment schedule into a dictionary (map).
# Schedule format is: 'due from date', 'due to date', 'process date'
processing_days = {}
f1 = open('processing_days.csv', 'r')
for line in f1:
    l = line[:-1].split(',')
    processing_days[l[0]] = (l[1], l[2])

# Assuming last processing was yesterday, work out whether
# any payments should be processed today
now = datetime.now()
itr_date = now
todays_date = formet_as_cps_date(now)
process_to_due_date = None
while True:
    k = formet_as_cps_date(itr_date)    # create the key to lookup day
    if k in processing_days:            # lookup day in processing days
        # check if payments due on day k should be processed today
        if processing_days[k][1] == todays_date:
            tmp = date_from_cps_format(processing_days[k][0])
            if (not process_to_due_date or process_to_due_date < tmp):
                process_to_due_date = tmp
        else:
            tmp = date_from_cps_format(processing_days[k][1])
            # if the new process date is in the future, then we are done today
            if tmp > now:
                break
        itr_date = itr_date + timedelta(days=1)
    else:   # something wrong if we can't find the date in our processing days
        break

# If payments should be processed today then process_to_due_date will be set
if not process_to_due_date:
    print('Not a processing day, can not continue')
    sys.exit()

# We now process all payments due up to and including process_to_due_date
print('Processing up to: ' + formet_as_cps_date(process_to_due_date))
# Load the schedules
data = json.load(open('schedules.json'))
for schedule in data['schedules']:
    freq_period = schedule['frequency'][1:].upper()
    freq_number = int(schedule['frequency'][0:1])
    if freq_period == 'W':
        delta = timedelta(days=(7 * freq_number))
    elif freq_period == 'M':
        delta = monthdelta(freq_number)
    else:
        continue    # not a valid schedule
    processed_up_to = date_from_iso_format(schedule['processedUpTo'])
    if processed_up_to == '':
        tmp = date_from_iso_format(schedule['paymentStartDate'])
    else:
        tmp = processed_up_to + delta
    while True:
        if (tmp <= process_to_due_date and tmp <= date_from_iso_format(schedule['paymentEndDate'])):
            make_payment(schedule, tmp.strftime('%d-%b') + ' PAYMENT' )
            processed_up_to = tmp
            tmp = processed_up_to + delta
        else:
            schedule['processedUpTo'] = format_as_iso_date(processed_up_to)
            break

# Lastly update the schedules
json.dump(data, open('schedules_update.json', 'w'), indent=2)
