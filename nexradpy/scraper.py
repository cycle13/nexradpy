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

# API Stuff
URL_DATE_FORM = '%Y/%m/%d'
LOCAL_DATE_FORM = '%Y_%m_%d'
START = datetime(2015, 1, 1) # .strftime(DATE_FORM)
END = datetime(2015, 6, 30)  # .strftime(DATE_FORM)
BASE_URL = 'http://noaa-nexrad-level2.s3.amazonaws.com'
SITE = 'KOKX' # Global for now but could easily be modified to use for many sites

'''
ONE-TIME FUNCTIONS
--Find files by date
----Takes Start / End dates
----Returns file list (without base URL, so file list can be used locally as well)
'''
def date_list(start, end):
	dates = []
	cur = start

	while cur <= end:
		print 'Appending: ', cur
		dates.append(cur)
		cur += timedelta(days=1)

	# return map(lambda x: BASE_URL + '/?prefix=' + x.strftime(DATE_FORM) + '/' + SITE, dates)
	return dates

'''
PARALLEL FUNCTIONS
'''
def urlify(date):
	return BASE_URL + '/?prefix=' + date.strftime(URL_DATE_FORM) + '/' + SITE

''' To make folder for day files '''
def locify(date):
	return date.strftime(LOCAL_DATE_FORM) + '_' + SITE

'''
Takes nodelist and returns relative filename for intra-day radar data
Taken directly from ____
'''
def get_text(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
    return ''.join(rc)

'''
Takes node from get_nodes, outfile strings
Downloads url, unzips, writes intra-day radar data to outfile
'''
def download_one(_node_url, outfile):
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

'''
Wrapper around get_one
--Takes URLified date
--Returns ??
'''
def get_files(date):
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




































def test():
	date = "2016/01/01"
	site = "KGSP"
	bucketURL = "http://noaa-nexrad-level2.s3.amazonaws.com"
	dirListURL = bucketURL+ "/?prefix=" + date + "/" + site

	print "listing files from %s" % dirListURL
	xmldoc = minidom.parse(urlopen(dirListURL))
	itemlist = xmldoc.getElementsByTagName('Key')
	print len(itemlist) , "keys found..."

# test()

'''
Need to confirm that the id-making scheme above is sufficient 
to identify a gate in space!

A couple problems come to mind: 
-- Sweeps could start at different rays across files
-- Files could be missing rays, which would throw off the indexing

To check--
	Write two CSVs of complete data (all gates, first sweep) from one intraday file
	Check, line by line, that lon / lat is the same for each ray-gate id
'''
def test_ids():
	intraday_file = 5
	d1 = datetime(2014, 1, 8)
	d2 = datetime(2015, 5, 10)

	d_urls = map(lambda x: BASE_URL + '/?prefix=' + x.strftime(DATE_FORM) + '/' + SITE, [d1,d2])

	tables = ['t1.csv', 't2.csv']

	# for i, u in enumerate(d_urls):
	# 	xmldoc = minidom.parse(urlopen(u))
	# 	nodelist = map(lambda x: x.childNodes, xmldoc.getElementsByTagName('Key'))
	# 	# nodelist = xmldoc.getElementsByTagName('Key')
	# 	# print(get_text(nodelist[intraday_file].childNodes))

	# 	t = get_text(nodelist[intraday_file])
	# 	rad_file = t.split('/')[-1].split('.')[0]

	# 	print('Getting: ', t)
	# 	get_one(nodelist[intraday_file], rad_file)

	# 	with open(tables[i], 'w+') as f:
	# 		flatten(rad_file, f)
	# 		f.close()

	f1 = open('t1.csv', 'rt')
	f2 = open('t2.csv', 'rt')

	print(len(f1.readlines(), f2.readlines()))

	line1 = f1.readline()
	line2 = f2.readline()

	while line1:
		if line1 != '':

			line1 = line1.split(',')
			line2 = line2.split(',')

			coords1 = (line1[2], line1[3])
			coords2 = (line2[2], line2[3])

			if coords1 != coords2:
				print('Not equal!')

		line1 = f1.readline()
		line2 = f2.readline()

# test_ids()
