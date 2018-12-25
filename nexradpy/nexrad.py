import pyart
import os
import math

OUTFILE = '/Users/clancygreen/Dropbox/Uber/Data/Precipitation/sample3.csv'
BASE = '/Users/clancygreen/Dropbox/Uber/Data/Precipitation/Sample NEXRAD Level 3 Files/'
INDIRS = ['NWS_NEXRAD_NXL3_KOKX_20140703000000_20140703235959',
		  'NWS_NEXRAD_NXL3_KOKX_20140516000000_20140516235959',
		  'NWS_NEXRAD_NXL3_KOKX_20140715000000_20140715235959']


## DAA: One hour precip (.13 nm x 1 deg)
## N1P: One hour precip (1.1 nm x 1 deg)
## Three hour precip (1.1 nm x 1 deg)
## DTA: Storm total (.13 x 1 deg)\
## OHA: One hour precip (1.1 x 1 deg)
## Differential reflectivity (vertical / horizontal radar pulse diff)
## NAR: Base reflectivity
## N1R: Base reflectivity
## NBR: Base reflectivity
## N2R: Base reflectivity
## NOQ: Digital base reflectivity
## NAQ: Digital base reflectivity
## N1Q: Digital base reflectivity
## NBQ: Digital base reflectivity
## N2Q: Digital base reflectivity
## -- Vary the elevation angle 
PRODUCTS = ['DAA','N1P','N3P','DTA','OHA','N0R','NAR','N1R','NBR','N2R','NOQ','NAQ','N1Q','NBQ','N2Q']
OVERWRITE = False

NYC = {
	'name': 'NYC',
	'a_s': 264,
	'a_e': 266,
	'd_s': 91250,
	'd_e': 95500
}

LGA = {
	'name': 'LGA',
	'a_s': 263,
	'a_e': 265,
	'd_s': 84500,
	'd_e': 87500
}

JFK = {
	'name': 'JFK',
	'a_s': 251,
	'a_e': 253,
	'd_s': 78250,
	'd_e': 81500
}

STATS = [NYC, LGA, JFK]


def get_days(folder):
	'''Takes folder holding lvl. 3 day folders
	To return list of day folders'''
	days = []
	for (dirpath, dirnames, filenames) in os.walk(folder):
		continue

def file_list(folder, product):
	'''Takes folder and product code
	Returns all files in folder matching given product code'''
	files = []
	for (dirpath, dirnames, filenames) in os.walk(folder):
		files.extend(filenames) ## Extend is in place whereas + creates new list
	
	## Filter files based on product code
	files = filter(lambda x: product in x, files)
	
	return files


def get_time(filename):
	'''Takes filename from filelist
	Returns (hour, minute)
	To be called in add_sample'''
	month = filename[-8:-6]
	day = filename[-6:-4]
	hour = filename[-4:-2]
	minute = filename[-2:]
	
	## Replace with dict for legibility and forcing deliberate unpacking
	return (month, day, hour, minute)


def flatten(outfile, infile, stat, prod):
	'''Takes outfile name (global) and infile name (from file_list)
	Writes rainfall from infile to outfile
	NOTE: Does not handle opening / closing outfile!'''	
	# print infile
	try:
		radar = pyart.io.nexradl3_read.read_nexrad_level3(infile)
	except IOError:
		print 'No such file'
	except NotImplementedError:
		print 'Product' + prod + ' not implemented'

	## Azimuth start and end indices (also degrees)
	## --based on ad hoc trig calcs (EPSG 2263)
	a_s = stat['a_s']
	a_e = stat['a_e']

	## Range start and end indices (multiples of distance in m)
	## --based on ad hoc distance calcs (EPSG 2263)
	meters_between = int(radar.range['meters_between_gates'])
	r_s = int(math.floor(stat['d_s']/meters_between))
	r_e = int(math.ceil(stat['d_e']/meters_between))

	## Looking a little like spaghetti
	for i in range(len(radar.gate_longitude['data'][a_s:a_e])):
		for j in range(len(radar.gate_longitude['data'][a_s:a_e][i][r_s:r_e])):
			
			## Get radar measurements
			ray_angle = i + a_s ## Equal to the azimuth angle
			gate_dist = radar.range['data'][r_s:r_e][j] ## One dim array (meters)
			lon = radar.gate_longitude['data'][a_s:a_e][i][r_s:r_e][j]
			lat = radar.gate_latitude['data'][a_s:a_e][i][r_s:r_e][j]

			try:
				ref = radar.fields['radar_estimated_rain_rate']['data'][a_s:a_e][i][r_s:r_e][j]
			except KeyError:
				ref = radar.fields['reflectivity']['data'][a_s:a_e][i][r_s:r_e][j]

			## Get time 
			mnth = get_time(infile)[0]
			day = get_time(infile)[1]
			hr = get_time(infile)[2]
			mnt = get_time(infile)[3]
			
			## Maybe also re-write to return values, but not write out
			## Re-write to avoid manual ordering!
			values = (stat['name'],prod,ray_angle, gate_dist, lon, lat, ref, mnth, day, hr, mnt)
			outfile.write('%s,%s,%d,%d,%s,%s,%s,%s,%s,%s,%s\r\n' % values)


def main():
	if OVERWRITE:
		try:
			print 'Re-writing...'
			os.remove(OUTFILE)
		except OSError:
			print 'No existing file. Starting from scratch...'
			return

	## Append days
	out = open(OUTFILE, 'a')
	## Avoid manual ordering!
	out.write('name,product,azimuth,dist,lon,lat,observation,month,day,hour,minute\r\n') 

	## To be replaced with iterable from get_days()
	abs_dirs = [BASE + d for d in INDIRS]

	for d in abs_dirs:
		print 'flattening ', d, "..."
		for s in STATS:
			print '-----------------------------' + s['name'] + '--------------------------------'
			for p in PRODUCTS:
				print p
				for f in file_list(d, p):
					flatten(out, d + '/' + f, s, p)
		
	out.close()

main()