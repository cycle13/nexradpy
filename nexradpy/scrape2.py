import os
import gzip

from xml.dom import minidom
from sys import stdin
from urllib.request import urlopen
from subprocess import call
from io import StringIO
from datetime import datetime, timedelta

# see https://www1.ncdc.noaa.gov/pub/data/radar/bdp/scripts/
URL_DATE_FORM = '%Y/%m/%d'
LOCAL_DATE_FORM = '%Y_%m_%d'
START = datetime(2015, 1, 1) # .strftime(DATE_FORM)
END = datetime(2015, 6, 30)  # .strftime(DATE_FORM)
BASE_URL = 'http://noaa-nexrad-level2.s3.amazonaws.com'
SITE = 'KOKX'


def date_list(start, end):
    dates = []
    cur = start

    while cur <= end:
        print('Appending: ', cur)
        dates.append(cur)
        cur += timedelta(days=1)
    
    return dates


def urlify(date):
    return BASE_URL + '/?prefix=' + date.strftime(URL_DATE_FORM) + '/' + SITE


def localify(date):
    return date.strftime(LOCAL_DATE_FORM) + '_' + SITE


def get_text(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)

    return ''.join(rc)


def get_files_by_date(date):
    xmldoc = minidom.parse(urlopen(urlify(date)))
    itemlist = xmldoc.getElementsByTagName('Key')

    for i, item in enumerate(itemlist):
        t = get_text(item.childNodes)
        node_url = BASE_URL + '/' + t
        intraday_file = t.split('/')[-1].split('.')[0]

        if intraday_file[0:4] == SITE and i == 0:
            print(node_url)
        elif intraday_file[0:3] == 'NWS':
            print('Not sure what these files are: ', node_url)
        else:
            print('Unrecognizable node name: ', node_url)


def get_files_by_range(date_list):
    for date in date_list:
        get_files_by_date(date) 


if __name__ == "__main__":
    '''print files found between start and end dates'''
    get_files_by_range(date_list(START, END))
