import os
from nexradpy.scrape import asos as scrape_asos
from datetime import datetime

## script to get gauge metadata (AWOS and ASOS site lat lons for all states)
## allow for possibility of getting availability by time

## globals
START = datetime(2014, 4, 1)
END = datetime(2014, 4, 2)
ASOS_OUTFILE = './nexradpy/asos_metadata.csv'

def get_asos_metadata(start, end):
    '''
    args:
        start, end timestamp (one day for purpose of metadata)
    returns:
        TODO: rewrite to return list of lines starting with headers!
              will allow for writes to CSV, JSON, GeoJSON, etc
    '''
    stations = scrape_asos.get_stations_from_networks(scrape_asos.STATES)

    rows = []
    for i, station in enumerate(stations):
        data = scrape_asos.get_data_by_station(station, start, end)
        
        if i is 1:
            data = data.split('\n')[5:6]
        else:
            data = data.split('\n')[6]

        rows += [line for line in data]       
    
    return rows


def main():
    print(get_asos_metadata(START, END))
    

if __name__ == '__main__':
    main()
