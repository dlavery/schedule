# Schedule
Schedule payment events.

This is a prototype to schedule payment events according to a BACS-like calendar provided in the file processing_days.csv. Test are available in testschedule.py.

The script schedule.py will process a payment schedule file in JSON format, generate a BACS-like payment instruction file based on this schedule and the BACS calendar, and create an updated schedule file for input into the next run. In the real world this would be an updated schedule in a no-SQL database such as MongoDB.

To see the file formats involved simply run the tests in testschedule.py.
