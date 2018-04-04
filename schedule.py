import sys
import os
import json
from datetime import date
from datetime import datetime
from datetime import timedelta
from monthdelta import monthdelta

class Schedule:

    def __init__(self):
        self.processing_days = {}
        try:
            os.remove('payments.csv')
        except FileNotFoundError:
            pass

    # Create a BACS format string from a date
    def formet_as_bacs_date(self, d):
        if d:
            return d.strftime('%d-%b-%Y') # e.g. 24-Jan-2018
        else:
            return ''

    # Create a date from a BACS format string
    def date_from_bacs_format(self, bacs):
        if bacs:
            return datetime.strptime(bacs, '%d-%b-%Y')
        else:
            return ''

    # Create an ISO date format string from a date
    def format_as_iso_date(self, d):
        if d:
            return d.strftime('%Y-%m-%d')
        else:
            return ''

    # Create a date from an ISO format string
    def date_from_iso_format(self, iso):
        if iso:
            return datetime.strptime(iso,'%Y-%m-%d')
        else:
            return ''

    # Make a payment
    def make_payment(self, schedule, reference, fh):
        s = schedule['payee']['name'] + '|' \
        + schedule['payee']['sortCode'] + '|' \
        + schedule['payee']['account'] + '|' \
        + reference + '|' + \
        str('%.2f' % schedule['amount'])
        fh.write(s + '\n')
        print('PAYMENT: ' + s)

    # Get BACS payment schedule into a dictionary (map).
    # Schedule format is: 'due from date', 'due to date', 'process date',
    # index is 'due from date'
    def get_schedule(self):
        f1 = open('processing_days.csv', 'r')
        for line in f1:
            l = line[:-1].split(',')
            self.processing_days[l[0]] = (l[1], l[2])
        f1.close()

    # Find the future date where payments due up to and including
    # this date should be processed today
    def find_forward_date(self):
        now = datetime.now()
        itr_date = now
        todays_date = self.formet_as_bacs_date(now)
        process_to_due_date = None
        while True:
            k = self.formet_as_bacs_date(itr_date)    # create the key to lookup day
            if k in self.processing_days:            # lookup day in processing days
                # check if payments due on day k should be processed today
                if self.processing_days[k][1] == todays_date:
                    tmp = self.date_from_bacs_format(self.processing_days[k][0])
                    if (not process_to_due_date or process_to_due_date < tmp):
                        process_to_due_date = tmp
                else:
                    tmp = self.date_from_bacs_format(self.processing_days[k][1])
                    # if the new process date is in the future, then we are done today
                    if tmp > now:
                        break
                itr_date = itr_date + timedelta(days=1)
            else:   # something wrong if we can't find the date in our processing days
                break
        return process_to_due_date

    # Assuming last processing was yesterday, work out whether
    # any payments should be processed today and process them
    def process(self):
        payment_file = open('payments.csv','w')
        self.get_schedule()
        now = datetime.now()
        itr_date = now
        todays_date = self.formet_as_bacs_date(now)
        process_to_due_date = self.find_forward_date()

        # If payments should be processed today then process_to_due_date will be set
        if not process_to_due_date:
            print('Not a processing day, can not continue')
            return

        # We now process all payments due up to and including process_to_due_date
        print('Processing up to: ' + self.formet_as_bacs_date(process_to_due_date))
        # Load the schedules from file
        f1 = open('schedules.json')
        data = json.load(f1)
        f1.close()
        for schedule in data['schedules']:
            freq_period = schedule['frequency'][1:].upper()
            freq_number = int(schedule['frequency'][0:1])
            if freq_period == 'W':
                delta = timedelta(days=(7 * freq_number))
            elif freq_period == 'M':
                delta = monthdelta(freq_number)
            else:
                continue    # not a valid schedule
            processed_up_to = self.date_from_iso_format(schedule['processedUpTo'])
            if processed_up_to == '':
                tmp = self.date_from_iso_format(schedule['paymentStartDate'])
            else:
                tmp = processed_up_to + delta
            while True:
                if (tmp <= process_to_due_date and tmp <= self.date_from_iso_format(schedule['paymentEndDate'])):
                    self.make_payment(schedule, tmp.strftime('%d-%b') + ' PAYMENT', payment_file)
                    processed_up_to = tmp
                    tmp = processed_up_to + delta
                else:
                    # update the schedule
                    schedule['processedUpTo'] = self.format_as_iso_date(processed_up_to)
                    break

        # Close payments file
        payment_file.close()

        # Lastly write the schedules back to file
        f2 = open('schedules_update.json', 'w')
        json.dump(data, f2, indent=2)
        f2.close()

if __name__ == '__main__':
    sched = Schedule()
    sched.process()
