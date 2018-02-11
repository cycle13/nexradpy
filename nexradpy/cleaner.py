# import pyart # comment out until modifying radar data due to slow load

'''
Takes filename from filelist
Returns (hour, minute)
To be called in add_sample
'''
def get_time(filename):
	pass

'''
Takes infile name (outfile from get_one) and outfile (global?)
Writes rainfall from infile to outfile
NOTE: Does not handle opening / closing outfile!
'''	
def flatten(infile, outfile):
	radar = pyart.io.read_nexrad_archive(infile)

	for i in range(len(radar.gate_longitude['data'])):
		for j in range(len(radar.gate_longitude['data'][i])):
			if i < 720: 
				ray_id = (i + 1) % 720 # to keep with 1-indexed IDs
				gate_id = (i * 720) + j + 1
				lon = radar.gate_longitude['data'][i][j]
				lat = radar.gate_latitude['data'][i][j]
				ref = radar.fields['reflectivity']['data'][i][j]

				# outfile.write('%d,%d,%s,%s,%s\r\n' % (ray_id, gate_id, lon, lat, ref))
			else:
				return