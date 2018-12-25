#!/usr/bin/env python3

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import pyart
import rtree
from shapely.geometry import Point, box


INDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'data/raw/temp'))
INFILE = '/KOKX20150505_050626_V06.gz'
POINTS_IN_GRID = 200
BBOX = [-74.363177, 40.460969, -73.632802, 40.901954]


def inter_points(pts, target_shape):
    '''
    '''
    spatial_index = pts.sindex
    possible_matches_index = list(spatial_index.intersection(target_shape.bounds))
    possible_matches = pts.iloc[possible_matches_index]
    
    return possible_matches[possible_matches.intersects(target_shape)]


def get_grid(radar, xy_len, fields):
    '''
    args: radar pyart obj, xy_len (int) points to have in each dimension, list of fields (strs)
    returns: grid pyart obj
    TODO: correct grid limits to bounding box
    '''
    gatefilter = pyart.filters.GateFilter(radar)
    gatefilter.exclude_transition()
    
    grid = pyart.map.grid_from_radars(
            (radar,), gatefilters=(gatefilter, ),
            grid_shape=(1, xy_len, xy_len),
            grid_limits=((2000, 2000), (-123000.0, 123000.0), (-123000.0, 123000.0)),
            fields=['reflectivity'])

    return grid


def get_grid_ibounds(grid, bbox):
    '''
    takes: grid pyart obj, list of coordinate boundaries
    returns: 4-tuple of bounds (outer min, outer max, inner min, inner max)
    '''
    grid_lat = [lat for arr in grid.point_latitude['data'][0] for lat in arr]
    grid_lon = [lon for arr in grid.point_longitude['data'][0] for lon in arr]
    grid_ij = [(i,j) for i, arr in enumerate(grid.point_longitude['data'][0]) for j,n in enumerate(arr)]

    grid_lon = []
    grid_ij = []
    for i, arr in enumerate(grid.point_longitude['data'][0]):
        for j, lon in enumerate(arr):
            grid_lon.append(lon)     
            grid_ij.append((i,j))

    # assumes lat, lon coordinates of points are indexed the same way in grid
    # see test/experiment.py for a rough check
    geometry = [Point(xy) for xy in zip(grid_lon, grid_lat)]
    
    # set up spatial join
    df = pd.DataFrame()
    point_gdf = gpd.GeoDataFrame(df, crs=4326, geometry=geometry)
    point_gdf['grid_index'] = grid_ij

    # restrict points to those within box
    point_gdf = inter_points(point_gdf, box(*bbox))

    iindexes = []
    jindexes = []
    for ij in point_gdf['grid_index']:
        iindexes.append(ij[0])
        jindexes.append(ij[1])
    
    # i indexes outermost grid array
    i_min = min(iindexes)
    i_max = max(iindexes)

    # j indexes inner grid array
    # could get min, max j within i, but min(min) and max(max) won't take much more space 
    # since grid is rectangular
    j_min = min(jindexes)
    j_max = max(jindexes)
    
    return (i_min, i_max, j_min, j_max)


if __name__ == '__main__':
    global radar, grid_ibounds
    radar = pyart.io.read(INDIR + INFILE) 
    grid = get_grid(radar, POINTS_IN_GRID, fields=['reflectivity'])
    grid_ibounds = get_grid_ibounds(grid, BBOX)
    print(grid_ibounds)
