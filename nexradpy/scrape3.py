import os
import gzip
import urllib
import urllib2

# default in listday
from xml.dom import minidom
from sys import stdin
from urllib import urlopen
from subprocess import call

from StringIO import StringIO
from datetime import datetime, timedelta

## API Stuff
## Re-write for level 3!
URL_DATE_FORM = '%Y/%m/%d'
LOCAL_DATE_FORM = '%Y_%m_%d'
START = datetime(2015, 1, 1) # .strftime(DATE_FORM)
END = datetime(2015, 6, 30)  # .strftime(DATE_FORM)
BASE_URL = 'http://noaa-nexrad-level2.s3.amazonaws.com'
SITE = 'KOKX' # Global for now but could easily be modified to use for many sites

'''ONE-TIME FUNCTIONS
--Find files by date
----Takes Start / End dates
----Returns file list (without base URL, so file list can be used locally as well)'''
def date_list(start, end):
	dates = []
	cur = start

	while cur <= end:
		print 'Appending: ', cur
		dates.append(cur)
		cur += timedelta(days=1)

	# return map(lambda x: BASE_URL + '/?prefix=' + x.strftime(DATE_FORM) + '/' + SITE, dates)
	return dates


def urlify(date):
	'''PARALLEL FUNCTIONS'''
	return BASE_URL + '/?prefix=' + date.strftime(URL_DATE_FORM) + '/' + SITE


def locify(date):
	''' To make folder for day files '''
	return date.strftime(LOCAL_DATE_FORM) + '_' + SITE


def get_text(nodelist):
	'''Takes nodelist and returns relative filename for intra-day radar data
	Taken directly from ____'''
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
    return ''.join(rc)


def download_one(_node_url, outfile):
	'''Takes node from get_nodes, outfile strings
	Downloads url, unzips, writes intra-day radar data to outfile'''
	# node_url = BASE_URL + '/' + get_text(node)
	req = urllib2.Request(_node_url)

	# See ______
	req.add_header('Accept-encoding', 'gzip')
	response = urllib2.urlopen(req)
	buf = StringIO(response.read())
	data = gzip.GzipFile(fileobj = buf).read()

	with open(outfile, 'w+') as o:
		o.write(data)
		o.close()

	# radar = pyart.io.read_nexrad_archive(outfile)

	return # could return outfile, but may be confusing

def delete_one(outfile):
	pass


def get_files(date):
	'''Wrapper around get_one
	--Takes URLified date
	--Returns ??'''	
	xmldoc = minidom.parse(urlopen(urlify(date))) # modify to urlify date
	# nodelist = map(lambda x: x.childNodes, xmldoc.getElementsByTagName('Key'))
	itemlist = xmldoc.getElementsByTagName('Key')

	day_root = date.strftime(LOCAL_DATE_FORM)
	if not os.path.isdir(day_root):
		os.makedirs(day_root)

	for i, item in enumerate(itemlist):
		# Could encapsulate this in get_node(node)
		# Would take node, date

		# Format URL and local file name
		t = get_text(item.childNodes)
		node_url = BASE_URL + '/' + t
		intraday_file = t.split('/')[-1].split('.')[0]

		if intraday_file[0:4] == SITE and i == 0:
			outfile = day_root + '/' + intraday_file
			download_one(node_url, outfile)
			# do stuff
			# delete_one(outfile)
			print outfile
		elif intraday_file[0:3] == 'NWS':
			print 'Not sure what these files are...'
		else:
			print 'Unrecognizable node name: ', intraday_file

def main():
	# Would parallelize over date_list
	for day in date_list(START, END):
		get_files(day)

main()