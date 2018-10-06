import nexradaws
from datetime import datetime

## globals
START = datetime(2015, 1, 1)
END = datetime(2015, 6, 30)
SITE = 'KOKX'

conn = nexradaws.NexradAwsInterface()


def log_availability(start, end, site):
    '''
    takes start and end dates
    checks that radar is available year(s) is available for years, months, days
    returns <some> information on availability of scans for time period
    '''
    pass


def get_scans(start, end, site):
    '''
    takes start and end dates and radar site, e.g., KOKX
    returns list of available scans
    wrapper for get_avail_scans
    '''
    pass


def download_range(i, j, loc, threads):
    '''
    takes start and end indices (w.r.t scan list) and download location
    takes #threads to allow this func to be parallelized instead
    downloads a slice of scan list to given loc
    returns list of successful downloads (nexradaws default) and failed downloads
    '''
    pass
