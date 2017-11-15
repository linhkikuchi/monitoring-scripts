#!/usr/bin/python

# run by crontab
# removes any files in /log/ older than 7 days

from pathlib import Path
import arrow, os

filesPath = "/nagios-data/log/archives"

criticalTime = arrow.now().shift(hours=+5).shift(days=-7)

for item in Path(filesPath).glob('*'):
    if item.is_file():
        itemTime = arrow.get(item.stat().st_mtime)
        if itemTime < criticalTime:
            #remove it
            print ("remove file: "+str(item.absolute()))
            os.remove(str(item.absolute()))