#!/usr/bin/env python3

import os
import numpy as np
import matplotlib.pyplot as plt
import pyart
import rtree
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box

from context import utils


INDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data/raw/temp'))
INFILE = '/KOKX20150505_050626_V06.gz'

POINTS_IN_GRID = 1000
BBOX = [-74.363177, 40.460969, -73.632802, 40.901954]


radar = pyart.io.read(INDIR + INFILE)

print('')
print('Meters between gates:', radar.range['meters_between_gates'])
print('')
print('Fields:', radar.fields.keys())
print('')


## corrections
## check return type
# radar_reflectivity = pyart.correct.despeckle_field(radar, 'reflectivity')
# radar = pyart.correct.correct_bias(radar)


## retrievals
## last three err bc missing fields
rr_z = pyart.retrieve.est_rain_rate_z(radar)
# rr_kdp = pyart.retrieve.est_rain_rate_kdp(radar)
# rr_hydro = pyart.retrieve.est_rain_rate_hydro(radar)
# hydroclass = pyart.retrieve.hydroclass_semisupervised(radar)


## mapping to cartesian grid
# mask out last 10 gates of each ray, this removes the "ring" around th radar.
radar.fields['reflectivity']['data'][:, -10:] = np.ma.masked

# exclude masked gates from the gridding
gatefilter = pyart.filters.GateFilter(radar)
gatefilter.exclude_transition()
gatefilter.exclude_masked('reflectivity')

# perform Cartesian mapping, limit to the reflectivity field.
grid = pyart.map.grid_from_radars(
    (radar,), gatefilters=(gatefilter, ),
    grid_shape=(1, 241, 241),
    grid_limits=((2000, 2000), (-123000.0, 123000.0), (-123000.0, 123000.0)),
    fields=['reflectivity'])

print(grid.fields)

# create the plot
fig = plt.figure()
ax = fig.add_subplot(111)
ax.imshow(grid.fields['reflectivity']['data'][0], origin='lower')
plt.show()


## get lat, lons from grid
print(grid.point_longitude)
print(grid.point_latitude)

# note that lens come from grid_shape
print(len(grid.point_longitude['data'][0][0]))
print(len(grid.point_longitude['data'][0]))

# if from the same radar, do these grids change by scan?
# if not, can get 2-d indexes of points in box one time and access
# data by index directly
# test by loading another scan
radar2 = pyart.io.read(INDIR + '/KOKX20150505_055459_V06.gz')


# note: may be good for timing to create global with time spent
# 		can parametrize timing to take name of global?
@utils.timing
def check_time_and_grid_equality():

	radar2.fields['reflectivity']['data'][:, -10:] = np.ma.masked

	gatefilter = pyart.filters.GateFilter(radar2)
	gatefilter.exclude_transition()
	gatefilter.exclude_masked('reflectivity')

	grid2 = pyart.map.grid_from_radars(
		(radar2,), gatefilters=(gatefilter, ),
		grid_shape=(1, 241, 241),
		grid_limits=((2000, 2000), (-123000.0, 123000.0), (-123000.0, 123000.0)),
		fields=['reflectivity'])

	if grid.point_longitude['data'][0][0].all() == grid2.point_longitude['data'][0][0].all():
			print('\n grid is (probably) identical!')

check_time_and_grid_equality()

# long coefficient comes out of @utils.timing above
print('lower bound is approx.', 
	0.029849982261657713 / 60 * 6 * 24 * 30 * 6, 
	'hours for 6 months of level 2 files')


@utils.timing
def test_grid_trim():
	## test restricting grid and getting point indexes
	grid_lat = []
	for arr in grid.point_latitude['data'][0]:
		for lat in arr:
			grid_lat.append(lat)

	# grid_lat = [lat for lat in arr for arr in grid.point_latitude['data'][0]]
	print(len(grid_lat))

	grid_lon = []
	for arr in grid.point_longitude['data'][0]:
		for lon in arr:
			grid_lon.append(lon)

	print(len(grid_lon))

	# assumes lat, lon coordinates of points are indexed the same way in grid
	geometry = [Point(xy) for xy in zip(grid_lon, grid_lat)]

	df = pd.DataFrame()
	point_gdf = gpd.GeoDataFrame(df, crs=4326, geometry=geometry)

	# plot point_gdf for comparison with points in box
	point_gdf.plot()
	plt.show()

	bbox = box(*BBOX)

	# index and join grid points to box
	spatial_index = point_gdf.sindex
	possible_matches_index = list(spatial_index.intersection(bbox.bounds))
	possible_matches = point_gdf.iloc[possible_matches_index]
	return possible_matches[possible_matches.intersects(bbox)]

points_in_box_gdf = test_grid_trim()
points_in_box_gdf.plot()
plt.show()
