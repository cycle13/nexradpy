#!/usr/bin/env python3

import sys
import json
import time
#import requests ## better python3 requests library maybe?
from urllib.request import urlopen
from datetime import datetime

## see: https://github.com/akrherz/iem/blob/master/scripts/asos/iem_scraper_example.py
## globals
MAX_ATTEMPTS = 6
BASE_URL = 'http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?'
STATES = '''AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME
 MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT
 WA WI WV WY'''.replace('\n', '').replace('\t', '').split(' ')
START = datetime(2014, 4, 1)
END = datetime(2014, 9, 30)


def download_data(uri):
    '''
    args:
        uri (string): URL to fetch
    returns:
        string data
    '''
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            data = urlopen(uri, timeout=300).read().decode('utf-8')
            if data is not None and not data.startswith('ERROR'):
                return data
        except Exception as exp:
            print('download_data(%s) failed with %s' % (uri, exp))
            time.sleep(5)
        attempts += 1

    print('Exhausted attempts to download, returning empty data')
    return ''


def get_stations_from_networks(state_list):
    '''
    args:
        list of states (state abbrev. strings, e.g., 'VA')
    returns:
        list of stations (SIDs)
    '''
    stations = []
    networks = [f'{state}_ASOS' for state in state_list]
       
    ## IEM has Iowa AWOS sites in own labeled network
    if 'IA' in state_list:
        networks.append('AWOS')
    
    for network in networks:
        # get metadata
        print('Getting site IDs for ', network)
        uri = f'https://mesonet.agron.iastate.edu/geojson/network/{network}.geojson'
        jdict = json.load(urlopen(uri))
        
        for site in jdict['features']:
            stations.append(site['properties']['sid'])

    return stations


def get_data_by_station(station, start, end):
    '''
    args:
        one station (sid), start date (datetime obj) and end date
    returns:
        data (small enough = ~2mb for 13000 obs or 5 months of <hourly data, 
              comma delimited, headers begin on fifth line if valid download -->
              see download_data)
    '''
    uri = BASE_URL + 'data=all&tz=Etc/UTC&format=comma&latlon=yes&'
    uri += start.strftime('year1=%Y&month1=%m&day1=%d&')
    uri += end.strftime('year2=%Y&month2=%m&day2=%d&')
    uri += f'&station={station}'

    print('Print downloading data for', station, 'between', start, 'and', end)
    return download_data(uri)


if __name__ == '__main__':
    data = get_data_by_station(get_stations_from_networks(STATES)[0], START, END)
    print('headers:', data.split('\n')[5])
    print(len(data.split('\n')), 'observations')
    print(sys.getsizeof(data) / 1000000, 'mb')
