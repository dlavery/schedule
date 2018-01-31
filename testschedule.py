import unittest
import json
from datetime import date
from datetime import datetime
from datetime import timedelta
from monthdelta import monthdelta
from schedule import Schedule

class TestSchedule(unittest.TestCase):

    def setUp(self):
        data = {}
        data['schedules'] = []
        todays_date = date.today()
        
        fh = open('processing_days.csv', 'r')
        processing_days = {}
        for line in fh:
            l = line[:-1].split(',')
            processing_days[l[0]] = (l[1], l[2])
        fh.close()        

        # Schedule 1 - multiple weekly payments due
        base_date = todays_date + timedelta(days=2)
        data['schedules'].append({ \
            "payee": {"name": "Jane Doe", "sortCode": "01-01-01", "account": "12345678"}, \
            "amount": 123.4, \
            "frequency": "1W", \
            "paymentStartDate": (base_date - timedelta(days=28)).isoformat(), \
            "paymentEndDate": (base_date + timedelta(days=364)).isoformat(), \
            "processedUpTo": (base_date - timedelta(days=21)).isoformat() \
        })

        # Schedule 2 - no payments due
        base_date = todays_date - timedelta(days=7)
        data['schedules'].append({ \
            "payee": {"name": "John Doe", "sortCode": "02-02-02", "account": "23456789"}, \
            "amount": 155.34, \
            "frequency": "1M", \
            "paymentStartDate": base_date.isoformat(), \
            "paymentEndDate": (base_date + timedelta(days=365)).isoformat(), \
            "processedUpTo": base_date.isoformat() \
        })

        # Schedule 3 - 1 monthly payment due
        base_date = todays_date + timedelta(days=1)
        data['schedules'].append({ \
            "payee": {"name": "Bob Smith", "sortCode": "03-03-03", "account": "34567890"}, \
            "amount": 134, \
            "frequency": "1M", \
            "paymentStartDate": (base_date - monthdelta(3)).isoformat(), \
            "paymentEndDate": (base_date + monthdelta(9)).isoformat(), \
            "processedUpTo": (base_date - monthdelta(1)).isoformat() \
        })

        # Schedule 4 - Brand new weekly schedule, 1 payment due
        base_date = todays_date
        data['schedules'].append({ \
            "payee": {"name": "Alice Smith", "sortCode": "04-04-04", "account": "45678901"}, \
            "amount": 151.01, \
            "frequency": "1W", \
            "paymentStartDate": base_date.isoformat(), \
            "paymentEndDate": (base_date + timedelta(days=365)).isoformat(), \
            "processedUpTo": "" \
        })

        # Schedule 5 - Brand new weekly schedule, no payment due
        base_date = todays_date + timedelta(days=7)
        data['schedules'].append({ \
            "payee": {"name": "Joe Jones", "sortCode": "05-05-05", "account": "56789012"}, \
            "amount": 78.3, \
            "frequency": "1W", \
            "paymentStartDate": base_date.isoformat(), \
            "paymentEndDate": (base_date + timedelta(days=365)).isoformat(), \
            "processedUpTo": "" \
        })

        # Schedule 6 - 1 four-weekly payment due
        base_date = todays_date + timedelta(days=2)
        data['schedules'].append({ \
            "payee": {"name": "Jo Jones", "sortCode": "06-06-06", "account": "67890123"}, \
            "amount": 176.21, \
            "frequency": "4W", \
            "paymentStartDate": (base_date - timedelta(weeks=8)).isoformat(), \
            "paymentEndDate": (base_date + timedelta(weeks=44)).isoformat(), \
            "processedUpTo": (base_date - timedelta(weeks=4)).isoformat() \
        })

        # Schedule 7 - no payments due (sometimes)
        base_date = todays_date + timedelta(days=3)
        if base_date >= datetime.strptime(processing_days[base_date.strftime('%d-%b-%Y')][1], '%d-%b-%Y').date():
            self.schedule7_expected = True
        else:
            self.schedule7_expected = False
        data['schedules'].append({ \
            "payee": {"name": "Harry X", "sortCode": "07-07-07", "account": "78901234"}, \
            "amount": 119.35, \
            "frequency": "1W", \
            "paymentStartDate": (base_date - timedelta(weeks=1)).isoformat(), \
            "paymentEndDate": (base_date + timedelta(weeks=51)).isoformat(), \
            "processedUpTo": (base_date - timedelta(weeks=1)).isoformat() \
        })

        fh = open('schedules.json', 'w')
        json.dump(data, fh, indent=2)
        fh.close()

    def test_schedule(self):
        sched = Schedule()
        sched.process()
        # check payments
        f1 = open('payments.csv', 'r')
        todays_date = date.today()
        # expect 3 equal payments to Jane Doe
        i = 0
        while i < 3:
            l = f1.readline()[:-1].split('|')
            self.assertEqual(l[0], 'Jane Doe')
            self.assertEqual(l[4], '123.40')
            i = i + 1
        # expect 1 payment to Bob Smith
        l = f1.readline()[:-1].split('|')
        self.assertEqual(l[0], 'Bob Smith')
        self.assertEqual(l[4], '134.00')
        # expect 1 payment to Alice Smith
        l = f1.readline()[:-1].split('|')
        self.assertEqual(l[0], 'Alice Smith')
        self.assertEqual(l[4], '151.01')
        # expect 1 payment to Jo Jones
        l = f1.readline()[:-1].split('|')
        self.assertEqual(l[0], 'Jo Jones')
        self.assertEqual(l[4], '176.21')
        # maybe a payment to Harry X
        l = f1.readline()[:-1].split('|')
        if self.schedule7_expected:
            self.assertEqual(l[0], 'Harry X')
            self.assertEqual(l[4], '119.35')
        else:
            # no more payments
            self.assertEqual(l, [''])

        f1.close()

        # check new schedules
        f2 = open('schedules_update.json', 'r')
        data = json.load(f2)
        # expect processed up to date for Jane Doe is today + 2 days
        self.assertEqual(data['schedules'][0]['payee']['name'], 'Jane Doe')
        self.assertEqual(data['schedules'][0]['processedUpTo'], (todays_date + timedelta(days=2)).isoformat())
        # expect processed up to date for John Doe is unchanged
        self.assertEqual(data['schedules'][1]['payee']['name'], 'John Doe')
        self.assertEqual(data['schedules'][1]['processedUpTo'], (todays_date - timedelta(days=7)).isoformat())
        # expect processed up to date for Bob Smith is today + 1 day
        self.assertEqual(data['schedules'][2]['payee']['name'], 'Bob Smith')
        self.assertEqual(data['schedules'][2]['processedUpTo'], (todays_date + timedelta(days=1)).isoformat())
        # expect processed up to date for Alice Smith is today
        self.assertEqual(data['schedules'][3]['payee']['name'], 'Alice Smith')
        self.assertEqual(data['schedules'][3]['processedUpTo'], todays_date.isoformat())
        # expect processed up to date for Joe Jones is empty
        self.assertEqual(data['schedules'][4]['payee']['name'], 'Joe Jones')
        self.assertEqual(data['schedules'][4]['processedUpTo'], '')
        # expect processed up to date for Jo Jones is today + 2
        self.assertEqual(data['schedules'][5]['payee']['name'], 'Jo Jones')
        self.assertEqual(data['schedules'][5]['processedUpTo'], (todays_date + timedelta(days=2)).isoformat())
        # expect processed up to date for Harry X is unchanged (sometimes)
        if self.schedule7_expected:
            self.assertEqual(data['schedules'][6]['payee']['name'], 'Harry X')
            self.assertEqual(data['schedules'][6]['processedUpTo'], (todays_date + timedelta(days=3)).isoformat())
        else:
            self.assertEqual(data['schedules'][6]['payee']['name'], 'Harry X')
            self.assertEqual(data['schedules'][6]['processedUpTo'], (todays_date - timedelta(days=4)).isoformat())

        f2.close()

if __name__ == '__main__':
    unittest.main()
